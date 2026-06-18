// generate deployment.sh based on user defined deployment definition

package main

import (
	"fmt"
	"os"
	"os/exec"
)

func main() {

	generateDeploysh()
	cmd := exec.Command("bash", "./deploy.sh")

	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	err := cmd.Run()
	if err != nil {
		fmt.Printf("Error executing script: %s\n", err)
		return
	}
}

func generateDeploysh() {

}
