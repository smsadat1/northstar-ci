# Northstar CI Architecture

## Overview

Northstar CI is a lightweight self-hostable distributed CI system designed to support hundreds of build executions and tests across distributed runner nodes.

The system is built around the idea of separating:

* Control Plane
* Execution Plane
* Storage Plane
* Logging / Observability Plane

Northstar CI evolved through multiple architectural revisions, gradually moving from a monolithic execution model toward a distributed and decoupled orchestration system.

---

# Architectural Goals

The primary goals of Northstar CI are:

* Lightweight self-hostable deployment
* Distributed execution support
* Deterministic and isolated task execution
* Horizontal runner scalability
* Minimal operational complexity
* Decoupled storage and execution
* Failure-tolerant orchestration
* Real-time log streaming


## High-Level Components

Northstar CI currently consists of:

* nsapi
* nsprovisioner
* nsrunner
* nslogger
* PostgreSQL
* Redis
* Celery
* S3-compatible object storage


# Current Execution Flow

## End-to-End Flow

1. Client parses YAML configuration
2. Client submits job metadata to nsapi
3. nsapi authenticates user
4. nsapi returns pre-signed S3 upload URL
5. Client uploads artifacts directly to S3
6. nsapi stores job metadata in Redis
7. nsprovisioner pulls pending jobs
8. nsprovisioner selects appropriate nsrunner
9. Task is distributed through Celery
10. nsrunner consumes task
11. nsrunner downloads artifacts from S3
12. Build stage executes
13. Run/test stage executes
14. Logs stream into nslogger
15. nslogger forwards logs to nsapi
16. nsapi streams logs to client via WebSocket
17. Execution data is persisted into PostgreSQL

---

# Architectural Characteristics

## Control Plane

Components:

* nsapi
* nsprovisioner

Responsibilities:

* Authentication
* Scheduling
* Metadata management
* State coordination

---

## Execution Plane

Components:

* nsrunner

Responsibilities:

* Task execution
* Isolation
* Resource enforcement
* Sandbox management

---

## Storage Plane

Components:

* S3
* PostgreSQL
* Redis

Responsibilities:

* Artifact storage
* Persistent job state
* Temporary metadata coordination

---

## Logging Plane

Components:

* nslogger

Responsibilities:

* Log aggregation
* Streaming
* Observability

---

# Future Considerations

Potential future improvements include:

* Explicit job lifecycle state machine
* Durable event-based scheduling
* Kafka-backed logging/event streams
* Artifact retention policies
* Runner execution leases
* Smarter scheduling heuristics
* Runner reservation models
* Distributed scheduler high availability
* Build cache layers
* Checkpoint-aware execution

---

# Conclusion

Northstar CI evolved from a monolithic prototype into a distributed execution-oriented CI architecture.

The current architecture emphasizes:

* Decoupled execution
* Distributed runners
* Lightweight self-hosting
* Storage independence
* Failure-aware orchestration
* Real-time observability

The system is intentionally designed to balance:

* Operational simplicity
* Horizontal scalability
* Strong execution isolation
* Minimal infrastructure complexity

while remaining practical for small-to-medium scale self-hosted CI deployments.
