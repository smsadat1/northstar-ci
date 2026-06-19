// change file name to taskline.go later

package execution

import "log"

// A taskline contains entire lifecycle for an instruction set (Lint -> Build -> Stage)
func taskline(nsris NSRInstructionSet) {

	// lint stage (optional) | Check whether this stage is actually defined
	if nsris.LintRuntime != "" && nsris.LintCommand != "" {
		rules := NSContainerRules{
			// system
			containerID: nsris.containerID,
			image:       imagemap[nsris.LintRuntime],
			command:     nsris.LintCommand,
			stage:       "LINT",

			// environment
			env:               nsris.BuildEnv,
			hostSrcpath:       nsris.filepath,
			containerDestPath: "/mnt",

			// rules
			memoryLimitMB:  nsris.MemoryLimitMB,
			pidLimit:       64,
			cpuShares:      nsris.CpuShares,
			cpuCores:       float64(nsris.CpuShares),
			noNewPrivilege: true,
			readOnlyRootfs: false,
			allowNetwork:   true,
			timeoutsec:     uint32(nsris.TimeoutSec),
		}

		if err := NSRExecute(rules); err != nil {
			nsrLogger("Halting task...")
			return
		}
	}

	// build stage (mandatory)
	if nsris.BuildCommand == "" || nsris.BuildRuntime == "" {
		nsrLogger("Build stage not properly defined\nHalting task...")
		return
	}

	rules := NSContainerRules{
		// system
		containerID: nsris.containerID,
		image:       imagemap[nsris.BuildRuntime],
		command:     nsris.BuildCommand,
		stage:       "BUILD",

		// environment
		env:               nsris.BuildEnv,
		hostSrcpath:       nsris.filepath,
		containerDestPath: "/mnt",

		// rules
		memoryLimitMB:  nsris.MemoryLimitMB,
		pidLimit:       64,
		cpuShares:      nsris.CpuShares,
		cpuCores:       float64(nsris.CpuShares),
		noNewPrivilege: true,
		readOnlyRootfs: false,
		allowNetwork:   true,
		timeoutsec:     uint32(nsris.TimeoutSec),
	}

	if err := NSRExecute(rules); err != nil {
		nsrLogger("Halting task...")
		return
	}

	// test stage (mandatory)
	if nsris.BuildCommand == "" || nsris.BuildRuntime == "" {
		log.Printf("Test stage not properly defined\nHalting task...\n")
		return
	}

	rules = NSContainerRules{
		// system
		containerID: nsris.containerID,
		image:       imagemap[nsris.TestRuntime],
		command:     nsris.TestCommand,
		stage:       "TEST",

		// environment
		// environment
		env:               nsris.BuildEnv,
		hostSrcpath:       nsris.filepath,
		containerDestPath: "/mnt",

		// rules
		memoryLimitMB:  nsris.MemoryLimitMB,
		pidLimit:       64,
		cpuShares:      nsris.CpuShares,
		cpuCores:       float64(nsris.CpuShares),
		noNewPrivilege: true,
		readOnlyRootfs: false,
		allowNetwork:   true,
		timeoutsec:     uint32(nsris.TimeoutSec),
	}

	if err := NSRExecute(rules); err != nil {
		nsrLogger("Halting task...")
		return
	}

	nsrLogger("All stages done")
}

func NSRExec(nsris NSRInstructionSet) error {
	// disable default timestamp
	log.SetFlags(0)

	// define the environment maps explicitly
	// lintEnvironment := map[string]string{
	// 	"FORCE_COLOR": "1", // Keep our CLI logs structured for UI rendering
	// }

	// buildEnvironment := map[string]string{
	// 	"PIP_CACHE_DIR":                 "/workspace/.pip-cache",
	// 	"PIP_DISABLE_PIP_VERSION_CHECK": "1",
	// }

	// testEnvironment := map[string]string{
	// 	"APP_ENV":      "ci",
	// 	"DATABASE_URL": "sqlite:///:memory:", // Isolated in-memory DB for tests
	// 	"DEBUG":        "False",
	// }

	// nsris := NSRInstructionSet{
	// 	containerID: "ci-pipeline-job-2026",
	// 	filepath:    "/tmp/nsci",

	// 	TimeoutSec:    120,
	// 	MemoryLimitMB: 512,
	// 	MaxStdoutKB:   1024,
	// 	CpuShares:     3,
	// 	DiskLimitMB:   200,

	// 	LintRuntime: "python-3.12",
	// 	LintCommand: "pip install --quiet flake8 && cd /mnt && flake8 .",
	// 	// LintCommand: "ls -la / && ls -la /tmp",
	// 	LintEnv: lintEnvironment,

	// 	BuildRuntime: "python-3.12",
	// 	BuildCommand: "if [ -f /mnt/requirements.txt ]; then pip install -r /mnt/requirements.txt; fi",
	// 	BuildEnv:     buildEnvironment,

	// 	TestRuntime: "python-3.12",
	// 	TestCommand: "pip install pytest && cd /mnt/tests && pytest -v",
	// 	TestEnv:     testEnvironment,
	// }

	taskline(nsris)
	return nil
}
