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

# Architecture v2 — Initial Distributed System

## Overview

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

# Architecture v3 — Decoupled Storage and Execution

## Overview

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

# Architecture v3 rev1 — Direct Client Uploads

## Overview

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

