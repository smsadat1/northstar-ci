package monitor

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"

	"golang.org/x/sys/unix"

	utils "northstar/utils"
)

func getCPUSample() (utils.NSRCPUSample, error) {
	file, err := os.Open("/proc/stat")
	if err != nil {
		return utils.NSRCPUSample{}, err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	if scanner.Scan() {
		fields := strings.Fields(scanner.Text())
		if len(fields) < 9 || fields[0] != "cpu" {
			return utils.NSRCPUSample{}, fmt.Errorf("unexpected /proc/stat format")
		}

		u, _ := strconv.ParseUint(fields[1], 10, 64)
		n, _ := strconv.ParseUint(fields[2], 10, 64)
		s, _ := strconv.ParseUint(fields[3], 10, 64)
		i, _ := strconv.ParseUint(fields[4], 10, 64)
		io, _ := strconv.ParseUint(fields[5], 10, 64)
		irq, _ := strconv.ParseUint(fields[6], 10, 64)
		sirq, _ := strconv.ParseUint(fields[7], 10, 64)
		stl, _ := strconv.ParseUint(fields[8], 10, 64)

		return utils.NSRCPUSample{
			User: u, Nice: n, System: s, Idle: i, Iowait: io, Irq: irq, Softirq: sirq, Steal: stl}, nil
	}

	return utils.NSRCPUSample{}, fmt.Errorf("Empty /proc/stat")
}

func calcCPUUsage(prev, curr utils.NSRCPUSample) float64 {
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
