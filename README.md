# Northstar CI

![Northstar CI Banner](docs/assets/banner.png)

Northstar CI is a lightweight self-hosted CI/CD platform designed for developers, homelabs, small teams, and independent projects that need fast, controllable, and transparent automation pipelines without relying on large cloud-based CI providers.

---

## Overview

Northstar CI focuses on distributed execution, simple pipeline definitions, and a Bring Your Own Runner (BYOR) philosophy.

Instead of centralizing execution on managed infrastructure, Northstar separates orchestration from execution, allowing runners to operate on user-owned hardware, homelabs, VPS instances, or dedicated machines.

Key goals:

- Simple CI/CD workflows
- Distributed runner architecture
- Self-hostable control plane
- Resource-limited execution
- Matrix build support
- Bring Your Own Runner (BYOR)
- Transparent pipeline definitions

---

## Architecture

![Northstar Architecture](docs/assets/archdiagram.png)

Northstar consists of several services:

| Service | Purpose |
|----------|----------|
| nsapi | API gateway and pipeline submission |
| nsprovisioner | Runner orchestration and job scheduling |
| nsrunner | Build execution and sandbox management |
| nshook | Webhook receiver for repository events |

---

## Core Concepts

### Bring Your Own Runner (BYOR)

Northstar allows users to contribute their own execution capacity.

Runners establish outbound connections to the orchestration layer and can execute pipelines on:

- Local machines
- Homelabs
- VPS instances
- Dedicated servers

This approach reduces centralized compute requirements while enabling horizontal scaling.

### Distributed Execution

Execution is separated from orchestration.

Control plane responsibilities:

- Pipeline scheduling
- Runner coordination
- Metadata management

Runner responsibilities:

- Build execution
- Test execution
- Deployment execution
- Resource enforcement

### Pipeline Definition

Northstar pipelines are defined using YAML.

Example:

```yaml
version: "0.0.1a"

target_fi
on:
  push:
    branch: main

jobs:

  limits:
    timeout_seconds: 10
    memory_mb: 256
    cpu_count: 2

  stages:

    - lint:
        runtime: python-3.12
        command: |
          python -m py_compile hudai.py

    - build:
        runtime: python-3.12
        command: |
          cp hudai.py /tmp/build/

    - test:
        runtime: python-3.12
        command: |
          python /tmp/build/hudai.py

    - deploy:
        runtime: alpine
        environment:
          SSH_HOST: "deploy.example.internal"
          SSH_USER: "deployer"
          SSH_PORT: "22"
        command: |
          echo "Deploying build to {environment}"
        steps:
          - scp -r /tmp/build deployer@deploy.example.internal:/opt/northstar/app
          - ssh deployer@deploy.example.internal "cd /opt/northstar/app && docker compose up -d"

```

## Features
- YAML-based pipelines
- Matrix builds
- Lint stage support
- Build stage support
- Test stage support
- Deploy stage support
- Distributed runners
- Resource limits
- Webhook integration
- CLI submission
- Self-hosted deployment

## Project Status

Northstar CI is currently under active development.

Current focus areas:

- Runner validation
- End-to-end pipeline testing
- Deployment workflows
- Documentation improvements

The architecture and APIs may change before the first stable release.


## Installation
### Control Plane
Instructions coming soon.

### Runner
Instructions coming soon.

## License

### GPL License