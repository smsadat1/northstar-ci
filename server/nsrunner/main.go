package main

import (
	"context"
	"log"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/types/known/timestamppb"

	dep "northstar/deployment"
	exc "northstar/execution"
	hb "northstar/monitor"
	pb "northstar/pb"
	utils "northstar/utils"
)

func main() {
	ctx := context.Background()

	// 1. Connect to remote nsprovisioner
	conn, err := grpc.NewClient("localhost:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("Failed to initialize grpc client: %v\n", err)
	}
	defer conn.Close()

	client := pb.NewTaskQueueServiceClient(conn)

	log.Println("gRPC client pipeline ready. Starting polling loop...")

	identity := &pb.RunnerIdentity{
		OwnerId:  "user-dev-99",
		RunnerId: "homelab-laptop-node-01",
		RunnerIp: "192.168.1.15",
		Version:  "v1.0.0",
	}

	for {
		// 2. Poll for pending task to recieve tasks
		taskResponse, err := client.FetchNextTask(ctx, identity)
		if err != nil {
			log.Printf("[Network Error] FetchNextTask failed: %v. Retrying in 10s...", err)
			time.Sleep(10 * time.Second)
			continue
		}

		if taskResponse.HasTask && taskResponse.Task != nil {
			log.Printf("[Worker Pipeline] Task detected. S3 Target: %s", taskResponse.Task.S3Url)

			// pass execution instruction downstream
			nsrcontainerrules := utils.NSRInstructionSet{
				Filepath: taskResponse.Task.S3Url,

				TimeoutSec:    time.Duration(taskResponse.Task.TimeoutSec),
				MemoryLimitMB: taskResponse.Task.MemoryLimitMb,
				MaxStdoutKB:   64000,
				CpuShares:     taskResponse.Task.CpuShares,
				DiskLimitMB:   256,

				LintRuntime: taskResponse.Task.LintRuntime,
				LintCommand: taskResponse.Task.LintCommand,
				LintEnv:     taskResponse.Task.LintEnv,

				BuildRuntime: taskResponse.Task.BuildRuntime,
				BuildCommand: taskResponse.Task.BuildCommand,
				BuildEnv:     taskResponse.Task.BuildEnv,

				TestRuntime: taskResponse.Task.TestRuntime,
				TestCommand: taskResponse.Task.TestCommand,
				TestEnv:     taskResponse.Task.TestEnv,
			}
			err = exc.NSRExec(nsrcontainerrules)
			if err != nil {
				log.Printf("Execution failed %v\n", err)
			}
		}

		if taskResponse.HasDeploy && taskResponse.Deploy != nil {
			log.Println("[Worker Pipeline] Deployment instruction detected")

			// pass deployment definition downstream
			nsrdeploydefs := utils.DeployInstructionSet{
				DeployRuntime: taskResponse.Deploy.DeployRuntime,
				DeployEnv:     taskResponse.Deploy.DeployEnv,
				Command:       taskResponse.Deploy.Command,
				Steps:         taskResponse.Deploy.Steps,
			}
			err = dep.NSRdeploy(nsrdeploydefs)
			if err != nil {
				log.Printf("Deployment failed %v\n", err)
			}
		}

		CpuPercent, MemPercent, DiskPercent := hb.GetHeartBeat()

		// push heartbeat metrics
		_, err = client.SendHeartBeat(ctx, &pb.NSRHeartBeat{
			OwnerId:  identity.OwnerId,
			RunnerId: identity.RunnerId,
			RunnerIp: identity.RunnerIp,
			Region:   "HOME",

			CpuPercent:  CpuPercent,
			MemPercent:  MemPercent,
			DiskPercent: DiskPercent,

			HeartbeatTime: timestamppb.Now(),
		})

		if err != nil {
			log.Printf("[Network Error] Heartbeat failed: %v", err)
		}
		time.Sleep(15 * time.Second)
	}
}
