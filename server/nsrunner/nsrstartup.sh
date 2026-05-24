#!/bin/bash

# Default values for flags 
SCALE_COUNT=1
REGION="Singapore"
PROVISIONER_HOST="localhost"
GRPC_PORT="50051"
IMAGE_TARGET="northstar/nsrunner:alpha1.0" # Default remote registry path
DETACH_FLAG="-d"
ENV_FILE_FLAG=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --scale)
      SCALE_COUNT="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --host)
      PROVISIONER_HOST="$2"
      shift 2
      ;;
    --logs)
      DETACH_FLAG=""   # Emptying this removes "-d", keeping the container attached in the foreground
      shift 1
      ;;
    --local)
      # Re-activated safely: switch target to local development build tag name
      IMAGE_TARGET="nsrunner:local" 
      shift 1
      ;;
    --env)
      # Fixed Assignment Bug: Added the '=' sign so Bash treats it as a variable string
      TARGET_ENV_FILE="$2"
      if [ -f "$TARGET_ENV_FILE" ]; then
        ENV_FILE_FLAG="--env-file $TARGET_ENV_FILE"
      else
        echo "Error: The specified environment file '$TARGET_ENV_FILE' does not exist."
        exit 1
      fi
      shift 2
      ;;
    *)
      echo "Unknown parameter passed: $1"
      echo "Usage: ./nsrstartup.sh --scale [num] --region [region] --host [prov_ip] [--logs] [--local] [--env path]"
      exit 1
      ;;
  esac
done

# If user requested --logs, scaling beyond 1 container will block the script on the first node.
if [[ -z "$DETACH_FLAG" && $SCALE_COUNT -gt 1 ]]; then
  echo "Warning: Using --logs with a --scale count greater than 1 will block the shell on the first container."
  echo "    Press Ctrl+C to terminate or run without --logs to scale cleanly in the background."
  echo "--------------------------------------------------------------------------------"
fi

echo "Scaling Up NorthstarCI Runner Cluster: spinning up ($SCALE_COUNT) runners in region [$REGION]..."
echo "Telemetry targets: gRPC Control Plane at $PROVISIONER_HOST:$GRPC_PORT"
echo "Targeted Engine Image: $IMAGE_TARGET"
if [[ -n "$ENV_FILE_FLAG" ]]; then
  echo "Injecting environment profile: $TARGET_ENV_FILE"
fi
echo "--------------------------------------------------------------------------------"

# loop to spin up the exact number of instances requested 
for ((i=1; i<=SCALE_COUNT; i++)); do
    # Generate explicit, isolated names and IDs for this specific instance run
    RUNNER_ID="nsrunner-node-$REGION-$i"
    HOST_WORKSPACE="/tmp"
    echo "Configuring [$RUNNER_ID]..."

    # establish the dedicated workspace directory on the host filesystem
    mkdir -p "$HOST_WORKSPACE/workspace"

    # tear down any lingering container with the same name to prevent collisions
    docker rm -f "$RUNNER_ID" >/dev/null 2>&1

    # Execute run with dynamic flags evaluated smoothly inline
    docker run $DETACH_FLAG $ENV_FILE_FLAG \
      --name "$RUNNER_ID" \
      --restart unless-stopped \
      -e RUNNER_ID="$RUNNER_ID" \
      -e REGION="$REGION" \
      -e PROVISIONER_ADDRESS="$PROVISIONER_HOST:$GRPC_PORT" \
      -e CELERY_CUSTOM_QUEUE="queue-$RUNNER_ID" \
      -v /var/run/containerd/containerd.sock:/var/run/containerd/containerd.sock \
      -v "$HOST_WORKSPACE/workspace:/tmp/workspace" \
      "$IMAGE_TARGET"

    # Streamlined logging logic
    if [[ -z "$DETACH_FLAG" ]]; then
      echo "[$RUNNER_ID] is up and broadcasting directly to stdout!"
    else
      echo "[$RUNNER_ID] is up and broadcasting in background!"
    fi
done

# Only display the summary table if running in detached background mode
if [[ -n "$DETACH_FLAG" ]]; then
  echo "--------------------------------------------------------------------------------"
  echo "Cluster scaling sequence complete. Current running cluster status:"
  docker ps --filter "name=nsrunner-node-" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
fi