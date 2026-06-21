package monitor

import (
	"fmt"
	"time"
)

func GetHeartBeat() (float64, float64, float64) {

	const interval uint8 = 15
	tick := time.NewTicker(time.Duration(interval) * time.Second)
	defer tick.Stop()

	fmt.Printf("Monitor service started with interval of: %v seconds\n", interval)

	// initial baseline reading for CPU calculation
	prevCPU, err := getCPUSample()
	if err != nil {
		fmt.Printf("Error getting initial CPU state: %v\n", err)
	}

	for range tick.C {

		currentCPU, err := getCPUSample()
		var cpuPercent float64
		if err == nil {
			cpuPercent = calcCPUUsage(prevCPU, currentCPU)
			prevCPU = currentCPU
		} else {
			fmt.Printf("[monitor] Error reading CPU: %v\n", err)
			break
		}

		memTotal, memavail, err := getMemoryUsage()
		var memUsed uint64
		var memPercent float64
		if err == nil {
			memUsed = memTotal - memavail
			memPercent = (float64(memUsed) / float64(memTotal)) * 100
		} else {
			fmt.Printf("Error reading memory %v\n", err)
			break
		}

		diskTotal, diskAvail, err := getDiskUsage("/")
		var diskUsed uint64
		var diskPercent float64
		if err == nil {
			diskUsed = diskTotal - diskAvail
			diskPercent = (float64(diskUsed) / float64(diskTotal)) * 100
		} else {
			fmt.Printf("Error reading disk %v\n", err)
			break
		}

		// output formatted telemetry
		// currentTime := time.Now().Format("2006/01/02 15:04:05")
		// fmt.Printf("[nsrunner] [%s] [METRICS] CPU: %.2f%% | MEM: %.2f%% (%dMB/%dMB) | DISK: %.2f%% (%dGB/%dGB)\n",
		// 	currentTime, cpuPercent,
		// 	memPercent, memTotal-memUsed, memTotal,
		// 	diskPercent, diskUsed/1024/1024/1024, diskTotal/1024/1024/1024,
		// )

		return cpuPercent, memPercent, diskPercent
	}

	return 0.0, 0.0, 0.0
}
