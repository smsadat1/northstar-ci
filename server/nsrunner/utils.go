package main

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

type NSRInstructionSet struct {
	// system
	containerID string
	filepath    string

	// resource limits
	TimeoutSec    time.Duration
	MemoryLimitMB uint64
	MaxStdoutKB   uint64
	CpuShares     uint64
	DiskLimitMB   uint64

	// stages
	LintRuntime string
	LintCommand string
	LintEnv     map[string]string

	BuildRuntime string
	BuildCommand string
	BuildEnv     map[string]string

	TestRuntime string
	TestCommand string
	TestEnv     map[string]string
}

type NSContainerRules struct {
	// system
	containerID string
	image       string
	command     string
	stage       string

	// environment
	hostSrcpath       string
	containerDestPath string
	env               map[string]string

	// rules
	memoryLimitMB  uint64
	pidLimit       int64
	cpuShares      uint64
	cpuCores       float64
	noNewPrivilege bool
	readOnlyRootfs bool
	allowNetwork   bool
	timeoutsec     uint32
}

// checks first whether requested image already exists
func pullContainerImage(imageName string, client *containerd.Client, ctx context.Context) containerd.Image {

	image, err := client.GetImage(ctx, imageName)

	if err == nil {
		fmt.Printf("[nsrunner] Image: %v found locally, skipping download\n", imageName)
		return image
	} else if errdefs.IsNotFound(err) {
		fmt.Printf("Image: %v not found locally, downloading image...\n", imageName)
		// download image
		image, err := client.Pull(ctx, imageName, containerd.WithPullUnpack)
		if err != nil {
			return nil
		}
		log.Printf("[nsrunner] Successfully downloaded and pulled image: %s\n", image.Name())
	} else {
		fmt.Printf("[nsrunner] Unexpected error occured querying image %v", err)
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
	rules NSContainerRules,
) []oci.SpecOpts {

	memoryBytes := uint64(rules.memoryLimitMB * 1024 * 1024)
	quota := int64(rules.cpuCores * 100000)
	period := uint64(100000)
	ociEnvs := parseToEnv(rules.env)

	opts := []oci.SpecOpts{
		// image
		oci.WithImageConfig(image),

		// resource limits
		oci.WithMemoryLimit(memoryBytes),
		oci.WithPidsLimit(rules.pidLimit),
		oci.WithCPUShares(rules.cpuShares),
		oci.WithCPUCFS(quota, period),

		// env
		oci.WithEnv(ociEnvs),

		// command to execute
		oci.WithProcessArgs("sh", "-c", command),
	}

	// file mount
	if rules.hostSrcpath != "" && rules.containerDestPath != "" {
		opts = append(opts, oci.WithMounts([]specs.Mount{
			{
				Type:        "bind",
				Source:      rules.hostSrcpath,
				Destination: rules.containerDestPath,
				/* "ro" makes it read-only for security, "rw" makes writable
				* "rbind" ensures sub-mounts are included, "nodev"/"nosuid" are standard sandbox protections
				 */
				Options: []string{"rbind", "ro", "nodev", "nosuid"},
			},
		}))
	}

	opts = []oci.SpecOpts{
		oci.WithCapabilities(stageCapabilities(rules.stage)),
	}

	if rules.readOnlyRootfs {
		opts = append(opts, oci.WithRootFSReadonly())
	}

	return opts
}

func enforceContainerLimits(
	ctx context.Context,
	client *containerd.Client,
	rules NSContainerRules,
	image containerd.Image,
) (containerd.Container, string, error) {

	snapshotID := rules.containerID + "-snapshot"

	opts := buildSpecOpts(image, rules.command, rules)

	container, err := client.NewContainer(
		ctx,
		rules.containerID,
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
		nsrLogger(scanner.Text())
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
func nsrLogger(logstring string) {
	log.Println("[nsrunner] " + logstring)
}
