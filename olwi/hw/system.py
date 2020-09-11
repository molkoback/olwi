import psutil

import time

def _cpu():
	return psutil.getloadavg()

def _uptime():
	tmp = int(time.time() - psutil.boot_time())
	s = tmp % 60
	tmp //= 60
	m = tmp % 60
	tmp //= 60
	h = tmp % 24
	tmp //= 24
	return tmp, h, m, s

def _memory():
	mem = psutil.virtual_memory()
	return {
		"total": round(mem.total/(1024**3), 1),
		"used": round(mem.used/(1024**3), 1)
	}

def _disk():
	disk = psutil.disk_usage("/")
	return {
		"total": round(disk.total/(1024**3), 1),
		"used": round(disk.used/(1024**3), 1)
	}

def readSystemParam():
	return {
		"Uptime": _uptime(),
		"CPU": _cpu(),
		"Memory": _memory(),
		"Disk": _disk()
	}
