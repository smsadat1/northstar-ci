# Northstar CI Architectural Evolution

## Architecture v1 — Monolithic Prototype

### Overview

The first version of Northstar CI was a fully monolithic prototype.

The primary goal of this architecture was to validate:

* End-to-end execution flow
* Task orchestration logic
* Runner execution lifecycle
* YAML parsing and task execution
* Basic CI pipeline feasibility

### Structure

All components existed inside a single application:

* API layer
* Scheduler
* Runner logic
* Execution engine
* Logging

Internal components communicated directly through function calls.

### Characteristics

#### Advantages

* Very simple deployment
* Fast iteration speed
* Easy debugging
* Minimal infrastructure requirements
* Useful for validating architectural assumptions

#### Limitations

* No horizontal scaling
* Tight coupling between components
* API lifecycle coupled to execution lifecycle
* Poor fault isolation
* No distributed runner support

### Conclusion

Architecture v1 successfully proved the feasibility of Northstar CI and established the foundation for later distributed designs.

---

## Architecture v2 — Initial Distributed System

### Overview

Architecture v2 introduced the first distributed decomposition of Northstar CI.

The monolith was split into multiple services to support:

* Distributed runners
* Horizontal scaling
* Independent execution nodes
* Better failure isolation

## Services Introduced

### nsapi

Responsible for:

* Receiving job specifications
* Receiving uploaded files
* Authentication
* API endpoints
* Streaming logs via WebSocket

### nsprovisioner

Responsible for:

* Scheduling jobs
* Selecting the best available runner
* Offloading execution tasks

### nsrunner

Responsible for:

* Executing CI jobs
* Running build/test tasks

## Communication Model

### File Transfer

In v2:

* nsapi received uploaded files from clients
* nsapi streamed files to nsprovisioner
* nsprovisioner streamed files to nsrunner via gRPC

### Metadata Flow

Job metadata was passed between services through Redis.

### Logging Flow

Logs from all services were:

* Published into Redis Pub/Sub
* Streamed through nsapi WebSocket connections

## Advantages

* First distributed runner support
* Better scaling potential
* Separation of scheduling and execution
* Independent runner nodes

## Limitations

### Tight Runtime Coupling

Services became tightly coupled because:

* File transfer depended on runtime connectivity
* gRPC streaming created heavy inter-service communication
* API layer remained in the data transfer path

### Data Plane and Control Plane Coupling

The same services handled:

* Scheduling
* File transfer
* Execution orchestration
* Metadata management

This increased system complexity.

---

## Architecture v3 — Decoupled Storage and Execution

### Overview

Architecture v3 introduced a major architectural redesign.

The focus shifted toward:

* Clear service boundaries
* Decoupled artifact storage
* Pull-based execution
* Independent execution workers

This revision separated:

* Control Plane
* Execution Plane
* Storage Plane
* Logging Plane

## Major Changes

### S3 Artifact Storage

The largest architectural change was introducing object storage.

Instead of streaming files through services:

* nsapi uploaded files into S3
* nsrunner downloaded files directly from S3

This removed:

* Runtime file streaming
* Heavy service coupling
* API bandwidth bottlenecks

### Removal of gRPC

gRPC-based artifact streaming was completely removed.

This significantly simplified:

* Service dependencies
* Runtime coordination
* Failure handling

### Pull-Based Runner Model

nsrunner became a pull-based worker.

Instead of receiving pushed file streams:

* nsrunner watched its task queue
* Pulled associated artifacts directly from S3
* Executed tasks independently

This improved:

* Fault tolerance
* Horizontal scalability
* Runner autonomy

### Dedicated Logging Service

nslogger was introduced.

Responsibilities:

* Centralized log aggregation
* Streaming logs to nsapi WebSocket layer
* Decoupling logging from execution

Redis Pub/Sub remained the initial transport layer.

The logging architecture was intentionally designed to allow future Kafka integration.

## Advantages

* Cleaner service responsibilities
* Decoupled storage model
* Reduced runtime dependencies
* Better scalability characteristics
* Independent execution workers
* More production-oriented design

## Limitations

### nsapi Still Handled File Ingress

Although files were stored in S3:

* nsapi still sat in the upload path
* API service still handled ingress bandwidth

This motivated the next revision.

---

## Architecture v3 rev1 — Direct Client Uploads

### Overview

Architecture v3 rev1 introduced direct client uploads using pre-signed URLs.

This removed nsapi from the file upload data path entirely.

The architecture became:

* Metadata through nsapi
* Artifacts directly uploaded to S3
* Execution workers independently downloading artifacts

## Flow Overview

### Job Submission

1. Client sends job specification metadata to nsapi
2. nsapi returns a pre-signed S3 upload URL
3. Client uploads artifacts directly to S3
4. nsapi stores metadata into Redis
5. nsprovisioner schedules execution
6. nsrunner consumes tasks and downloads artifacts from S3
7. Logs are aggregated through nslogger and streamed back to clients

## Advantages

### Complete Storage Decoupling

nsapi no longer handles:

* File uploads
* Artifact transfer bandwidth
* Multipart upload lifecycle

### Improved Scalability

This significantly improved:

* API scalability
* Upload throughput
* Memory efficiency
* Failure isolation

### Better Retry Semantics

Since artifacts exist independently in object storage:

* Upload retries become simpler
* Runner retries become easier
* Artifact availability becomes independent from services

## Remaining Challenges

### Eventual Consistency

Runners may occasionally receive tasks before uploads fully complete.

To address this:

* nsrunner performs retry logic while downloading artifacts

### Scheduler Complexity

As execution scale grows:

* scheduling heuristics
* retries
* runner allocation
* resource balancing

become increasingly difficult.

## Architecture v3 rev2 — Workspace Normalization

### Overview

Architecture v3 rev2 refined the responsibility boundaries introduced in v3 rev1.

While v3 rev1 introduced direct artifact uploads through pre-signed URLs, the backend still needed to reason about different workspace sources such as local files, local directories, and remote Git repositories.

v3 rev2 moved workspace preparation entirely to the client.

The architecture became:

* Client prepares execution workspace
* Client compresses workspace into a single archive
* Client uploads archive directly to object storage
* Backend treats all execution inputs identically

## Flow Overview

### Workspace Preparation

1. User specifies a local file, local directory, or remote repository
2. Client collects the execution workspace
3. If a remote repository is specified, the client clones it locally
4. Client compresses the workspace into a single archive
5. Client uploads the archive directly to object storage using a pre-signed URL
6. Client submits job metadata to nsapi
7. nsapi stores JobSpec metadata
8. nsprovisioner schedules execution
9. nsrunner downloads the workspace archive and executes the job

## Architectural Principle Introduced

### Workspace Normalization

All execution inputs are transformed into a common workspace representation before entering the control plane.

The backend no longer needs to differentiate between:

* Local files
* Local directories
* Git repositories

All inputs become:

* Workspace archive

This significantly reduces branching logic throughout the system.

## Advantages

### Simpler Backend Logic

The control plane now operates on a single execution artifact format.

This eliminates special handling for:

* Repository cloning
* Directory traversal
* File collection

### Reduced Service Complexity

Neither nsapi nor nsprovisioner need knowledge of workspace origins.

Execution orchestration becomes independent of input source.

### Consistent Runner Behavior

Runners always receive a normalized workspace package.

Execution preparation becomes predictable and easier to maintain.

## Remaining Challenges

### Client Responsibilities

The client now performs additional work:

* Repository cloning
* Workspace packaging
* Compression

This increases client complexity.

### Large Workspace Handling

Very large repositories may increase:

* Compression time
* Upload duration
* Client resource usage

These concerns may require optimization in future versions.


## Architecture v4 — Bring Your Own Runner (BYOR)

### Overview

Architecture v4 introduced the Bring Your Own Runner (BYOR) model.

Instead of provisioning and managing runners centrally, Northstar CI allows users to operate their own runner instances.

This fundamentally changes the deployment model of the platform.

The architecture became:

* Centralized control plane
* User-owned execution plane
* Pull-based runner communication
* Outbound-only connectivity

## Architectural Principle Introduced

### Runner Ownership Decentralization

Execution infrastructure is no longer owned by the platform.

Users provide execution capacity by running nsrunner instances on their own hardware.

Examples include:

* Homelabs
* Desktop computers
* Dedicated servers
* Virtual machines
* Self-hosted infrastructure

### Pull-Based Scheduling

Runners initiate communication with the control plane.

Instead of tasks being pushed to runners:

nsrunner requests work from nsprovisioner.

This allows operation behind:

* NAT
* Carrier-grade NAT (CGNAT)
* Firewalls
* Restricted home networks

## Flow Overview

### Runner Lifecycle

1. nsrunner starts on a user-managed machine
2. nsrunner authenticates with nsprovisioner
3. nsrunner registers capabilities and begins sending heartbeats
4. nsrunner periodically requests work
5. nsprovisioner assigns available jobs
6. nsrunner downloads required artifacts
7. nsrunner executes the workload
8. Logs and status updates are reported back to the platform

## Advantages

### Improved Accessibility

Users can contribute execution capacity without:

* Public IP addresses
* Port forwarding
* Inbound firewall rules

This greatly improves usability for self-hosted environments.

### Better Security Posture

Runners require only outbound connections.

No external system needs direct network access to execution nodes.

### Horizontal Scalability

Additional execution capacity can be added simply by launching new runner instances.

Scaling becomes independent of platform-managed infrastructure.

### Infrastructure Flexibility

Users may execute workloads on infrastructure they already own.

This reduces operational costs and increases deployment flexibility.

## Remaining Challenges

### Runner Authentication

The platform must securely manage:

* Runner registration
* Runner identity
* Authentication credentials
* Runner revocation

### Capability Discovery

Scheduling decisions require accurate runner metadata, including:

* CPU resources
* Memory capacity
* Available storage
* Runtime capabilities

### Offline Runner Handling

User-managed runners may:

* Disconnect unexpectedly
* Reboot
* Lose connectivity
* Become unavailable for extended periods

The scheduler must account for these situations.

### Trust and Verification

As execution moves to user-managed infrastructure, future versions may require stronger guarantees around:

* Job completion reporting
* Artifact integrity
* Execution verification
* Runner trust models

## Architecture v4 rev1 — Native Runner Runtime

### Overview

Architecture v4 rev1 replaced the original Python-based runner implementation with a native Go runtime.

This revision was driven by the introduction of the Bring Your Own Runner (BYOR) model in v4.

Rather than running inside a privileged container, nsrunner now executes directly on the host machine and communicates with containerd through its native Go APIs.

The architecture became:

* Native Go runner
* Direct containerd integration
* Host-level execution runtime
* Distributed executable distribution

## Architectural Principle Introduced

### Native Runtime Ownership

Execution infrastructure moved from:

* Python process orchestration
* Shell command execution
* nerdctl command parsing

to:

* Native containerd APIs
* Direct runtime control
* Host-level execution management

The runner became a standalone executable distributed to user-managed infrastructure.

## Flow Overview

### Execution Lifecycle

1. nsrunner starts on the host machine
2. nsrunner connects to nsprovisioner
3. nsrunner requests work
4. nsrunner receives a JobSpec
5. nsrunner interacts directly with containerd
6. Isolated execution environments are created
7. Execution completes
8. Cleanup is performed through containerd APIs

## Advantages

### Improved Performance

Direct runtime integration removes:

* CLI invocation overhead
* command parsing
* shell process creation

### Better Runtime Control

The runner gains direct access to:

* container lifecycle management
* execution state
* image management
* resource handling

### Simplified Distribution

The runner becomes:

* a standalone binary
* easier to install
* easier to distribute
* independent of Python runtime requirements

### Stronger Foundation for Parallel Execution

The Go runtime provides a stronger foundation for:

* concurrent task execution
* matrix builds
* future scheduler optimizations

## Remaining Challenges

### Host-Level Requirements

The runner now depends on:

* containerd availability
* containerd socket access
* host runtime configuration

### Runtime Compatibility

Different host environments may expose:

* varying containerd versions
* runtime configuration differences
* platform-specific behaviors

These require additional compatibility testing.

## Architecture v4 rev2 — Multi-Tenant Runner Ownership

### Overview

Architecture v4 rev2 introduced ownership-aware scheduling and execution.

As the platform evolved toward self-hosted runners, a mechanism was required to ensure jobs execute only on infrastructure owned by the corresponding user.

This revision introduced owner-based runner isolation.

The architecture became:

* Owner-aware scheduling
* Runner ownership tracking
* User-scoped execution
* Artifact integrity verification

## Architectural Principle Introduced

### Ownership Isolation

Each authenticated user receives a unique owner_id.

All runner instances register with an associated owner_id.

Job scheduling becomes ownership-aware, ensuring workloads execute only on infrastructure controlled by the corresponding user.

### Integrity Verification

Artifacts are verified after download through checksum validation.

Execution only proceeds after integrity checks succeed.

## Flow Overview

### Job Execution

1. User authenticates with the platform
2. User receives an owner_id
3. Runner registers with its owner_id
4. User submits a job
5. nsprovisioner locates runners matching the owner_id
6. nsrunner downloads workspace artifacts
7. Checksum validation occurs
8. Execution begins after successful verification

## Advantages

### Stronger Isolation

Jobs can only execute on:

* user-owned runners
* explicitly associated infrastructure

This prevents accidental cross-user execution.

### Better Scheduling Accuracy

The scheduler gains awareness of:

* runner ownership
* available execution capacity
* user-specific infrastructure

### Improved Artifact Safety

Checksum validation prevents execution of:

* incomplete downloads
* corrupted uploads
* partially transferred artifacts

## Remaining Challenges

### Runner Lifecycle Management

The platform must manage:

* runner registration
* ownership reassignment
* runner revocation

### Ownership Scaling

As user counts increase:

* ownership metadata
* scheduling efficiency
* runner discovery

become increasingly important concerns.

## Architecture v5 — Deployment and Event Automation

### Overview

Architecture v5 expanded Northstar from a CI platform into a CI/CD platform.

Two new services were introduced:

* nsdeploy
* nshook

These services extend the platform beyond execution by supporting deployment automation and external event integration.

The architecture became:

* Event-driven execution
* Deployment automation
* Dedicated webhook ingestion
* End-to-end CI/CD workflows

## Architectural Principle Introduced

### Separation of Execution and Deployment

Execution and deployment are treated as separate responsibilities.

nsrunner remains responsible for:

* workspace preparation
* isolated execution
* artifact generation

nsdeploy becomes responsible for:

* artifact deployment
* remote environment updates
* release delivery

### Dedicated Event Ingestion

Webhook handling moves into a dedicated service.

External systems no longer communicate directly with execution infrastructure.

## Flow Overview

### CI Flow

1. nshook receives webhook events
2. Event metadata is validated
3. JobSpec is generated
4. nsprovisioner schedules execution
5. nsrunner executes workload
6. Artifacts are produced

### Deployment Flow

1. nsrunner uploads artifacts to a registry
2. nsdeploy receives deployment instructions
3. nsdeploy connects to the target server through SSH
4. Deployment artifacts are retrieved
5. Deployment is performed

## Advantages

### Cleaner Service Boundaries

Responsibilities become clearly separated:

* nshook → event ingestion
* nsprovisioner → scheduling
* nsrunner → execution
* nsdeploy → deployment

### Git-Native Automation

The platform can now react automatically to:

* repository pushes
* merge requests
* pull requests
* release events

### Deployment Support

Northstar evolves beyond build automation and can participate in:

* application delivery
* release workflows
* deployment pipelines

## Remaining Challenges

### Deployment Reliability

Deployment workflows introduce new concerns:

* rollback handling
* deployment failures
* partial releases
* environment consistency

### Webhook Security

Webhook processing requires:

* signature verification
* replay protection
* source validation

### Registry Management

Artifact delivery introduces additional operational concerns:

* registry availability
* artifact retention
* version management
* deployment traceability
