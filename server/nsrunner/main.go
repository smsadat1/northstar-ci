package main

import (
	"context"
	"log"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/types/known/timestamppb"

	hb "northstar/monitor"
	pb "northstar/pb"
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
			// pass task downstream after dividing into execution and deployment
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
