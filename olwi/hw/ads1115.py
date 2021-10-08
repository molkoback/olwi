from olwi.weight_sensor import WeightSensor, WeightSensorException

import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import board
import busio

import asyncio
import time

class ADS1115(WeightSensor):
	def __init__(self, delay=0.250, avg=60):
		self.delay = delay
		self.avg = avg
		
		self.ads = ADS.ADS1115(busio.I2C(board.SCL, board.SDA))
		self.chan = AnalogIn(self.ads, ADS.P0, ADS.P1)
		self.ads.gain = 1
		
		self._lock = asyncio.Lock()
		self._stop = asyncio.Event()
		self._stopped = asyncio.Event()
	
	async def _loop(self):
		self._stop.clear()
		self._stopped.clear()
		await self.reset()
		while not self._stop.is_set():
			start = time.time()
			async with self._lock:
				V = self.chan.voltage
				now = time.time()
				self._values = [(V, t) for V, t in self._values if now-t <= self.avg]
				self._values.append((V, now))
			delta = self.delay - (time.time() - start)
			if delta > 0:
				await asyncio.sleep(delta)
		await self.reset()
		self._stopped.set()
	
	async def start(self):
		asyncio.get_event_loop().create_task(self._loop())
	
	async def stop(self):
		self._stop.set()
		await self._stopped.wait()
	
	async def reset(self):
		self._values = []
	
	def _convert(self, V):
		# TODO
		return 0.0
	
	async def weight(self):
		async with self._lock:
			sum = 0
			n = 0
			for V, _ in self._values:
				sum += V
				n += 1
		V = sum / n
		return self._convert(V), V
