package utils

import "time"

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
