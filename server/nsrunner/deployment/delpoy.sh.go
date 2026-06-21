// generate deployment.sh based on user defined deployment definition

package deployment

import (
	"bytes"
	"fmt"
	"html/template"
	"os"
	"os/exec"

	utils "northstar/utils"
)

const bashTemplates = `
#!/bin/sh
# Generated automatically by Northstar CI
set -e

# env vars
{{- range $key, $value := .DeployEnv}}
export {{$key}} = "{{$value}}"
{{- end}}

# commands
{{ .Command }}

# steps
{{- range .Steps }}
{{ . }}
{{- end }}
`

func NSRdeploy(instructions utils.DeployInstructionSet) error {

	generateDeploysh(instructions, "./deploy.sh")
	cmd := exec.Command("bash", "./deploy.sh")

	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	err := cmd.Run()
	if err != nil {
		fmt.Printf("Error executing script: %s\n", err)
		return err
	}

	return nil
}

func generateDeploysh(instructions utils.DeployInstructionSet, outputPath string) error {
	tmpl, err := template.New("deployScript").Parse(bashTemplates)
	if err != nil {
		return err
	}

	var buffer bytes.Buffer
	err = tmpl.Execute(&buffer, instructions)
	if err != nil {
		return err
	}

	// permission code 0755 to be auto executable
	err = os.WriteFile(outputPath, buffer.Bytes(), 0755)
	if err != nil {
		return err
	}

	return nil
}
