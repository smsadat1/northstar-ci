package utils

type NSRCPUSample struct {
	User, Nice, System, Idle, Iowait, Irq, Softirq, Steal uint64
}

type NSRHeartBeat struct {
	cpuPercent  float64
	memPercent  float32
	diskPercent float32
}
