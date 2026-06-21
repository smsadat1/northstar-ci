// change file name to taskline.go later

package execution

import (
	"log"

	utils "northstar/utils"
)

// A taskline contains entire lifecycle for an instruction set (Lint -> Build -> Stage)
func taskline(nsris utils.NSRInstructionSet) {

	// lint stage (optional) | Check whether this stage is actually defined
	if nsris.LintRuntime != "" && nsris.LintCommand != "" {
		rules := utils.NSContainerRules{
			// system
			Image:   imagemap[nsris.LintRuntime],
			Command: nsris.LintCommand,
			Stage:   "LINT",

			// environment
			Env:               nsris.BuildEnv,
			HostSrcpath:       nsris.Filepath,
			ContainerDestPath: "/mnt",

			// rules
			MemoryLimitMB:  nsris.MemoryLimitMB,
			PidLimit:       64,
			CpuShares:      nsris.CpuShares,
			CpuCores:       float64(nsris.CpuShares),
			NoNewPrivilege: true,
			ReadOnlyRootfs: false,
			AllowNetwork:   true,
			Timeoutsec:     uint32(nsris.TimeoutSec),
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

	rules := utils.NSContainerRules{
		// system
		Image:   imagemap[nsris.BuildRuntime],
		Command: nsris.BuildCommand,
		Stage:   "BUILD",

		// environment
		Env:               nsris.BuildEnv,
		HostSrcpath:       nsris.Filepath,
		ContainerDestPath: "/mnt",

		// rules
		MemoryLimitMB:  nsris.MemoryLimitMB,
		PidLimit:       64,
		CpuShares:      nsris.CpuShares,
		CpuCores:       float64(nsris.CpuShares),
		NoNewPrivilege: true,
		ReadOnlyRootfs: false,
		AllowNetwork:   true,
		Timeoutsec:     uint32(nsris.TimeoutSec),
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

	rules = utils.NSContainerRules{
		// system
		Image:   imagemap[nsris.TestRuntime],
		Command: nsris.TestCommand,
		Stage:   "TEST",

		// environment
		// environment
		Env:               nsris.BuildEnv,
		HostSrcpath:       nsris.Filepath,
		ContainerDestPath: "/mnt",

		// rules
		MemoryLimitMB:  nsris.MemoryLimitMB,
		PidLimit:       64,
		CpuShares:      nsris.CpuShares,
		CpuCores:       float64(nsris.CpuShares),
		NoNewPrivilege: true,
		ReadOnlyRootfs: false,
		AllowNetwork:   true,
		Timeoutsec:     uint32(nsris.TimeoutSec),
	}

	if err := NSRExecute(rules); err != nil {
		nsrLogger("Halting task...")
		return
	}

	nsrLogger("All stages done")
}

func NSRExec(nsris utils.NSRInstructionSet) error {
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
