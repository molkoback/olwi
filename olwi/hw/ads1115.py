from olwi.weight_sensor import WeightSensor, WeightSensorException

import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import board
import busio

import asyncio

class ADS1115(WeightSensor):
	def __init__(self):
		self.ads = ADS.ADS1115(busio.I2C(board.SCL, board.SDA))
		self.chan = AnalogIn(self.ads, ADS.P0, ADS.P1)
		self.ads.gain = 1
		
		self._lock = asyncio.Lock()
		self._stop = asyncio.Event()
		self._stopped = asyncio.Event()
		self._resetMeas()
	
	"""
	def _findGain(self):
		limit = max(abs(self.vrange[0]), abs(self.vrange[1]))
		if limit > 6.144:
			raise WeightSensorException("Invalid voltage range: {}-{}".format(self.vrange[0], self.vrange[1]))
		else:
			gain = 2/3
		if limit < 4.096:
			gain = 1
		if limit < 2.048:
			gain = 2
		if limit < 1.024:
			gain = 4
		if limit < 0.512:
			gain = 8
		if limit < 0.256:
			gain = 16
		return gain
	"""
	
	def _resetMeas(self):
		self._sums = [0.0, 0.0]
		self._n = 0
	
	def _read(self):
		# TODO
		raw = self.chan.voltage
		return 0.0, raw
	
	async def _loop(self, delay):
		self._stop.clear()
		self._stopped.clear()
		async with self._lock:
			self._resetMeas()
		
		while not self._stop.is_set():
			async with self._lock:
				weight, raw = self._read()
				self._sums[0] += weight
				self._sums[1] += raw
				self._n += 1
			await asyncio.sleep(delay)
		
		async with self._lock:
			self._resetMeas()
		self._stopped.set()
	
	async def start(self, delay=0.010):
		asyncio.get_event_loop().create_task(self._loop(delay))
	
	async def stop(self):
		self._stop.set()
		await self._stopped.wait()
	
	async def reset(self):
		pass
	
	async def weight(self, avg=True):
		if avg:
			async with self._lock:
				if self._n > 0:
					return self._sums[0]/self._n, self._sums[1]/self._n
		return self._read()
