/*
* NSRExecute()
* Creates containers via containerd to execute tasks in isolated environment
 */

package execution

import (
	"context"
	"log"

	containerd "github.com/containerd/containerd/v2/client"
	"github.com/containerd/containerd/v2/pkg/namespaces"
)

func NSRExecute(rules NSContainerRules) error {
	// init client and setup namespace
	client, err := containerd.New("/run/containerd/containerd.sock")
	if err != nil {
		log.Printf("[nsrunner] Failed to create containerd: %v", err)
		return err
	}
	defer client.Close()
	ctx := namespaces.WithNamespace(context.Background(), "go_example")

	// spawn container
	container, err := spawnContainer(ctx, client, rules)

	if err != nil {
		log.Printf("[nsrunner] Failed to spawn container: %v", err)
		return err
	}

	// delete container w/snapshot when main() exits
	defer container.Delete(ctx, containerd.WithSnapshotCleanup)

	// create and manage container
	err = createAndManageTask(container, ctx, rules)
	if err != nil {
		log.Printf("[nsrunner] Task management failed %v", err)
		return err
	}

	return nil
}
