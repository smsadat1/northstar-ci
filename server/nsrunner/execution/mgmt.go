package execution

import (
	"context"
	"fmt"
	"io"
	"log"
	"os"
	"syscall"
	"time"

	containerd "github.com/containerd/containerd/v2/client"
	"github.com/containerd/containerd/v2/pkg/cio"
	"github.com/containerd/errdefs"
)

func spawnContainer(
	ctx context.Context,
	client *containerd.Client,
	rules NSContainerRules,
) (containerd.Container, error) {

	image := pullContainerImage(rules.image, client, ctx)
	container, snapshotID, err := enforceContainerLimits(ctx, client, rules, image)

	if err != nil {
		log.Printf("[nsrunner] Failed created container with ID %s", container.ID())
		return nil, err
	}

	log.Printf("[nsrunner] Successfully created container with ID %s and snapshot with ID %v", container.ID(), snapshotID)

	return container, nil
}

func createAndManageTask(
	container containerd.Container,
	ctx context.Context,
	rules NSContainerRules,
) error {

	// synchronous unix pipe for read & write
	stdoutReader, stdoutWriter := io.Pipe()
	stderrReader, stderrWriter := io.Pipe()

	// pass the write end to containerd
	task, err := container.NewTask(ctx,
		cio.NewCreator(cio.WithStreams(os.Stdin, stdoutWriter, stderrWriter)))

	if err != nil {
		return err
	}
	// made sure to delete if something fails midway
	defer task.Delete(ctx)

	id := container.ID()
	netNS := fmt.Sprintf("/proc/%d/ns/net", task.Pid())

	// network
	if rules.allowNetwork {
		network, tmpNetCfgDir, err := setupNetwork()
		if err != nil {
			nsrLogger("Network setup failed during container initialization")
			return err
		}

		result, err := network.Setup(ctx, id, netNS)
		if err != nil {
			return err
		}
		nsrLogger("Network provisioned automatically! Container IP: %s\n", result.Interfaces["eth0"].IPConfigs[0].IP)

		defer network.Remove(ctx, id, netNS)
		defer os.RemoveAll(tmpNetCfgDir)
	}

	// get real time log stream
	go streamContainerLogs("", stdoutReader)
	go streamContainerLogs("", stderrReader)

	// get exit status channel
	statusC, err := task.Wait(ctx)
	if err != nil {
		return err
	}

	// start task execution
	if err := task.Start(ctx); err != nil {
		return err
	}
	nsrLogger("Task started successfully")

	timeoutDuration := time.Duration(rules.timeoutsec) * time.Second
	ctxTimeout, cancel := context.WithTimeout(ctx, timeoutDuration)
	defer cancel()

	// dynamic wait block
	select {
	case status := <-statusC:

		nsrLogger("Task completed.")
		if status.Error() != nil {
			return status.Error()
		}

	case <-ctxTimeout.Done():
		// force kill , just in case
		log.Printf("[nsrunner] Task exceeded set timeout %v\nStopping task...\n", rules.timeoutsec)
		if err := task.Kill(ctx, syscall.SIGTERM); err != nil {
			if errdefs.IsNotFound(err) {
				nsrLogger("Task finished right as timeout hit; ignoring 'not found' error.")
			} else {
				// genuine error
				return err
			}
		}
	}

	// block till exit status
	status := <-statusC
	if status.Error() != nil {
		return status.Error()
	}

	log.Printf("[nsrunner] Task exited with status code %v", status.ExitCode())

	return nil
}
