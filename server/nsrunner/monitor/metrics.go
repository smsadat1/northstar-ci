// get system data

package monitor

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"golang.org/x/sys/unix"
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

func getCPUSample() (CPUSample, error) {
	file, err := os.Open("/proc/stat")
	if err != nil {
		return CPUSample{}, err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	if scanner.Scan() {
		fields := strings.Fields(scanner.Text())
		if len(fields) < 9 || fields[0] != "cpu" {
			return CPUSample{}, fmt.Errorf("unexpected /proc/stat format")
		}

		u, _ := strconv.ParseUint(fields[1], 10, 64)
		n, _ := strconv.ParseUint(fields[2], 10, 64)
		s, _ := strconv.ParseUint(fields[3], 10, 64)
		i, _ := strconv.ParseUint(fields[4], 10, 64)
		io, _ := strconv.ParseUint(fields[5], 10, 64)
		irq, _ := strconv.ParseUint(fields[6], 10, 64)
		sirq, _ := strconv.ParseUint(fields[7], 10, 64)
		stl, _ := strconv.ParseUint(fields[8], 10, 64)

		return CPUSample{
			User: u, Nice: n, System: s, Idle: i, Iowait: io, Irq: irq, Softirq: sirq, Steal: stl}, nil
	}

	return CPUSample{}, fmt.Errorf("Empty /proc/stat")
}

func calcCPUUsage(prev, curr CPUSample) float64 {
	prevIdle := prev.Idle + prev.Iowait
	currIdle := curr.Idle + curr.Iowait

	prevNonIdle := prev.User + prev.Nice + prev.System + prev.Irq + prev.Softirq + prev.Steal
	currNonIdle := curr.User + curr.Nice + curr.System + curr.Irq + curr.Softirq + curr.Steal

	prevTotal := prevIdle + prevNonIdle
	currTotal := currIdle + currNonIdle

	totalDelta := currTotal - prevTotal
	idleDelta := currIdle - prevIdle

	if totalDelta == 0 {
		return 0.0
	}
	return (float64(totalDelta-idleDelta) / float64(totalDelta)) * 100
}

// parses memory info from /proc/meminfo and returns MB
func getMemoryUsage() (total uint64, available uint64, err error) {

	file, err := os.Open("/proc/meminfo")
	if err != nil {
		return 0, 0, err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	found := 0

	for scanner.Scan() {
		fields := strings.Fields(scanner.Text())
		if len(fields) < 2 {
			continue
		}

		if strings.HasPrefix(fields[0], "MemTotal") {
			total, _ = strconv.ParseUint(fields[1], 10, 64)
			found++
		} else if strings.HasPrefix(fields[0], "MemAvailable") {
			available, _ = strconv.ParseUint(fields[1], 10, 64)
			found++
		}

		if found == 2 {
			break
		}
	}

	// KB to MB
	return total / 1024, available / 1024, nil
}

// parses disk usage
func getDiskUsage(path string) (total uint64, available uint64, err error) {
	var stat unix.Statfs_t
	if err = unix.Statfs(path, &stat); err != nil {
		return 0, 0, err
	}

	total = stat.Blocks * uint64(stat.Bsize)
	available = stat.Bavail * uint64(stat.Bsize)
	return total, available, nil
}
