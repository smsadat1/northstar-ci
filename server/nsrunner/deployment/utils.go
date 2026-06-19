package deployment

type DeployInstructionSet struct {
	DeployRuntime string
	DeployEnv     map[string]string
	Command       string
	Steps         []string
}
