# Internal Service Architecture

# nsapi

## Responsibilities

nsapi is the primary control plane API service.

Responsibilities include:

* Authentication
* API endpoint handling
* YAML job specification intake
* WebSocket log streaming
* Issuing pre-signed S3 upload URLs
* Persisting job execution data
* Persisting API keys and user-related metadata

## Database Ownership

nsapi is currently the only service connected to PostgreSQL.

PostgreSQL stores:

* Users
* API keys
* Job execution history
* Build metadata
* Execution states

This design intentionally centralizes persistent state ownership.

## Logging

nsapi receives aggregated logs from nslogger and streams them to clients using WebSocket connections.

## Architectural Role

nsapi acts as:

* API gateway
* Authentication layer
* State ownership service
* User-facing control plane endpoint

---

# nsprovisioner

## Responsibilities

nsprovisioner is the scheduling and orchestration engine.

Responsibilities include:

* Reading job metadata from Redis
* Selecting appropriate runners
* Task distribution
* Runner allocation
* Monitoring runner heartbeats
* Failure detection
* Rescheduling failed jobs

## Scheduling Logic

### Single Command / Single File Jobs

Scheduling policy:

* Find first runner where system_load < 80%
* Offload task to that runner

### Pipeline Command / Multi-File Jobs

Scheduling policy:

* Find runner where system_load < 40%
* Allocate heavier tasks to less busy runners

### Matrix Builds

Scheduling policy:

* Find best available runner cluster
* If best runner is partially busy:

  * distribute matrix tasks across multiple runners

## Heartbeat Monitoring

nsprovisioner continuously monitors runner heartbeat payloads.

Heartbeat payloads contain:

* CPU usage
* Memory usage
* Disk usage
* Runner activity state

## Failure Handling

If a runner:

* Stops sending heartbeats
* Runs suspiciously long
* Becomes unresponsive

Then:

* Task is halted
* Runner execution is considered failed
* Job is rescheduled from the beginning
* Another runner is selected

## Architectural Role

nsprovisioner acts as:

* Scheduler
* Cluster orchestrator
* Task allocator
* Failure recovery controller

---

# nsrunner

## Responsibilities

nsrunner is the execution engine of Northstar CI.

Responsibilities include:

* Watching Celery task queues
* Pulling artifacts from S3
* Executing CI tasks
* Enforcing execution isolation
* Streaming logs

## Task Consumption

nsrunner watches its assigned Celery queue.

When a task arrives:

1. Retrieve associated artifacts from S3
2. Prepare execution environment
3. Execute build stage
4. Execute run/test stage
5. Stream logs continuously

## Two-Stage Execution Model

Northstar CI uses a two-stage execution isolation model.

---

### Stage 1 — Build Stage

Purpose:

* Compilation
* Dependency installation
* Build preparation

Permissions:

* Limited network access
* Read + Write filesystem access
* More tolerant resource limits
* Higher disk usage allowance
* Higher log streaming allowance

This stage is intentionally flexible because builds often require:

* Downloading dependencies
* Compiling code
* Generating build artifacts

---

### Stage 2 — Run/Test Stage

Purpose:

* Executing tests
* Running user code
* Deterministic execution

Restrictions:

* No network access
* No privilege escalation
* Read-only filesystem
* Strict memory limits
* Strict CPU limits
* Strict disk limits
* Strict log output limits

This stage prioritizes:

* Isolation
* Security
* Determinism
* Resource protection

## Architectural Role

nsrunner acts as:

* Execution worker
* Sandbox runtime
* Distributed compute node

---

# nslogger

## Responsibilities

nslogger is the centralized logging and observability service.

Responsibilities include:

* Receiving logs from services
* Aggregating logs
* Streaming logs toward nsapi
* Decoupling logging from execution services

## Current Transport Layer

Current implementation:

* Redis Pub/Sub

## Planned Future Direction

The logging layer is intentionally designed to support future Kafka integration.

Possible future benefits:

* Durable log streams
* Log replay
* Multiple consumers
* Analytics pipelines
* Better scalability

## Log Flow

1. nsapi streams logs to nslogger
2. nsprovisioner streams logs to nslogger
3. nsrunner streams logs to nslogger
4. nslogger forwards logs to nsapi
5. nsapi streams logs to clients via WebSocket

## Architectural Role

nslogger acts as:

* Centralized observability pipeline
* Log aggregation service
* Real-time streaming relay

