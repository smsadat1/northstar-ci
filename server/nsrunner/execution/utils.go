package execution

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"log"
	"time"

	containerd "github.com/containerd/containerd/v2/client"
	"github.com/containerd/containerd/v2/pkg/oci"
	"github.com/containerd/errdefs"
	"github.com/opencontainers/runtime-spec/specs-go"

	utils "northstar/utils"
)

var imagemap = map[string]string{
	// for C/C++
	"alpine": "docker.io/library/alpine:3.22",
	"gcc":    "docker.io/library/gcc:15",
	"clang":  "docker.io/library/silkeh/clang:20",

	"dotnet-10": "mcr.microsoft.com/dotnet/sdk:10.0",

	"go-1.26": "docker.io/library/golang:1.26-slim",
	"go-1.24": "docker.io/library/golang:1.24-slim",
	"go-1.22": "docker.io/library/golang:1.22-slim",

	"java-21": "docker.io/library/eclipse-temurin:21-jdk",
	"java-17": "docker.io/library/eclipse-temurin:17-jdk",

	"node-26": "docker.io/library/node:26-bookworm-slim",
	"node-24": "docker.io/library/node:24-bookworm-slim",
	"node-22": "docker.io/library/node:22-bookworm-slim",

	"python-3.13": "docker.io/library/python:3.13-slim",
	"python-3.12": "docker.io/library/python:3.12-slim",
	"python-3.11": "docker.io/library/python:3.11-slim",
	"python-3.10": "docker.io/library/python:3.10-slim",

	"rust-1.96": "docker.io/library/rust:1.96-slim",
	"rust-1.94": "docker.io/library/rust:1.94-slim",
	"rust-1.92": "docker.io/library/rust:1.92-slim",
}

// checks first whether requested image already exists
func pullContainerImage(imageName string, client *containerd.Client, ctx context.Context) containerd.Image {

	image, err := client.GetImage(ctx, imageName)

	if err == nil {
		nsrLogger("Image: %v found locally, skipping download\n", imageName)
		return image
	} else if errdefs.IsNotFound(err) {
		nsrLogger("Image: %v not found locally, downloading image...\n", imageName)
		// download image
		image, err := client.Pull(ctx, imageName, containerd.WithPullUnpack)
		if err != nil {
			return nil
		}
		nsrLogger("Successfully downloaded and pulled image: %s\n", image.Name())
	} else {
		nsrLogger("Unexpected error occured querying image %v", err)
		return nil
	}

	return image
}

func stageCapabilities(stage string) []string {
	switch stage {
	case "BUILD":
		return []string{"CAP_NET_RAW", "CAP_CHOWN", "CAP_SETUID", "CAP_SETGID"}
	case "LINT":
		return []string{"CAP_CHOWN"}
	case "TEST":
		return []string{"CAP_NET_RAW"}
	default:
		return nil // no capabilities for unknown stage
	}
}

func buildSpecOpts(
	image containerd.Image,
	command string,
	rules utils.NSContainerRules,
) []oci.SpecOpts {

	memoryBytes := uint64(rules.MemoryLimitMB * 1024 * 1024)
	quota := int64(rules.CpuCores * 100000)
	period := uint64(100000)
	ociEnvs := parseToEnv(rules.Env)

	opts := []oci.SpecOpts{
		// image
		oci.WithImageConfig(image),

		// resource limits
		oci.WithMemoryLimit(memoryBytes),
		oci.WithPidsLimit(rules.PidLimit),
		oci.WithCPUShares(rules.CpuShares),
		oci.WithCPUCFS(quota, period),

		// env
		oci.WithEnv(ociEnvs),
	}

	// file mount
	if rules.HostSrcpath != "" && rules.ContainerDestPath != "" {
		opts = append(opts, oci.WithMounts([]specs.Mount{
			{
				Type:        "bind",
				Source:      rules.HostSrcpath,
				Destination: rules.ContainerDestPath,
				/* "ro" makes it read-only for security, "rw" makes writable
				* "rbind" ensures sub-mounts are included, "nodev"/"nosuid" are standard sandbox protections
				 */
				Options: []string{"rbind", "ro", "nodev", "nosuid", "create=dir"},
			},
		}))
	}

	opts = []oci.SpecOpts{
		oci.WithCapabilities(stageCapabilities(rules.Stage)),
	}

	if rules.ReadOnlyRootfs {
		opts = append(opts, oci.WithRootFSReadonly())
	}

	// evaluated last to guarantee execution parameters survive
	if command != "" {
		processArgs := []string{"/bin/sh", "-c", command}
		opts = append(opts, oci.WithProcessArgs(processArgs...))
	}

	return opts
}

func enforceContainerLimits(
	ctx context.Context,
	client *containerd.Client,
	rules utils.NSContainerRules,
	image containerd.Image,
) (containerd.Container, string, error) {

	if image == nil {
		return nil, "", fmt.Errorf("cannot enforce limits: provided image object is nil")
	}

	fmt.Printf("Command: %v\n", rules.Command)

	snapshotID := rules.ContainerID + "-snapshot"

	opts := buildSpecOpts(image, rules.Command, rules)

	container, err := client.NewContainer(
		ctx,
		rules.ContainerID,
		containerd.WithNewSnapshot(snapshotID, image),
		containerd.WithNewSpec(opts...),
		// containerd.WithRuntime("runsc", nil), // gVisor interception
	)

	if err != nil {
		return nil, "", err
	}

	return container, snapshotID, nil
}

// stream real time logs from container
func streamContainerLogs(prefix string, reader io.Reader) {
	scanner := bufio.NewScanner(reader)
	for scanner.Scan() {
		fmt.Printf("%s\n", scanner.Text())
	}
}

func parseToEnv(envMap map[string]string) []string {
	envSlice := make([]string, 0, len(envMap))
	for k, v := range envMap {
		// formats the map pairs explicitly as "KEY=VALUE"
		envSlice = append(envSlice, fmt.Sprintf("%s=%s", k, v))
	}
	return envSlice
}

// logs with tag
func nsrLogger(format string, v ...interface{}) {
	currentTime := time.Now().Format("2006/01/02 15:04:05")
	prefix := fmt.Sprintf("[nsrunner] [%s] ", currentTime)
	log.Printf(prefix+format, v...)
}
