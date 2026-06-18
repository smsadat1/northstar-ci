package deployment

type DeployInstructionSet struct {
	deployRuntime string
	deployEnv     map[string]string
	command       string
	steps         []string
}
