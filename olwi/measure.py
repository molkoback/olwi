from olwi.device import Device

import asyncio
import logging
import time

class Measure:
	def __init__(self, cfg, device, storage, database):
		self.cfg = cfg
		self.device = device
		self.storage = storage
		self.database = database
		self._timeNext = None
		self._stop = None
		self._stopped = None
	
	def _resetTime(self):
		i = self.cfg.sensor.measInterval
		now = int(time.time())
		self._timeNext = now // i * i + i if i > 0 else now
	
	async def run(self):
		if self.database is not None:
			logging.info("Synchronizing database")
			await self.database.sync(self.storage)
		
		self._stop = asyncio.Event()
		self._stopped = asyncio.Event()
		
		self._resetTime()
		while not self._stop.is_set():
			delta = self._timeNext - time.time()
			if delta > 0:
				logging.debug("Sleeping {:.2f} seconds".format(delta))
				await asyncio.sleep(delta)
			
			meas = await self.device.read()
			logging.info("[{}] In: {:.1f}°C | Out: {:.1f}°C | Weight: {:.1f}g ({:.3f})".format(
				meas.DateTime.strftime("%H:%M:%S"),
				meas.TempIn, meas.TempOut,
				meas.Weight, meas.WeightRaw
			))
			
			await self.storage.put(meas)
			if self.database is not None:
				await self.database.insert(meas)
			
			self._timeNext += self.cfg.sensor.measInterval
		self._stopped.set()
	
	async def start(self):
		asyncio.get_event_loop().create_task(self.run())
	
	async def stop(self):
		self._stop.set()
		await self._stopped.wait()
