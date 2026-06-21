package utils

import "time"

type NSRInstructionSet struct {
	// system
	ContainerID string
	Filepath    string

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
	ContainerID string
	Image       string
	Command     string
	Stage       string

	// environment
	HostSrcpath       string
	ContainerDestPath string
	Env               map[string]string

	// rules
	MemoryLimitMB  uint64
	PidLimit       int64
	CpuShares      uint64
	CpuCores       float64
	NoNewPrivilege bool
	ReadOnlyRootfs bool
	AllowNetwork   bool
	Timeoutsec     uint32
}
