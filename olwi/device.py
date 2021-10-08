from olwi.motor import createMotor
from olwi.relay import createRelay
from olwi.temp_relay import createTempRelay
from olwi.temp_sensor import createTempSensor
from olwi.weight_sensor import createWeightSensor

import asyncio
from datetime import datetime
import enum
import logging
import time

class DeviceException(Exception):
	pass

class DeviceStatus(enum.Enum):
	MEASURE = 0
	DEICE = 1

class MeasurementError(enum.Enum):
	TEMPIN = 1
	TEMPOUT = 2
	WEIGHT = 4

class Measurement:
	def __init__(self):
		self.DateTime = datetime.utcnow()
		self.TempIn = 0.0
		self.TempInOffset = 0.0
		self.TempOut = 0.0
		self.TempOutOffset = 0.0
		self.Weight = 0.0
		self.WeightRaw = 0.0
		self.Status = DeviceStatus.MEASURE
		self.Errors = []
	
	@classmethod
	def fromdict(cls, dict):
		meas = cls()
		meas.DateTime = datetime.strptime(dict["DateTime"], "%Y-%m-%d %H:%M:%S")
		meas.TempIn = dict["TempIn"]
		meas.TempInOffset = dict["TempInOffset"]
		meas.TempOut = dict["TempOut"]
		meas.TempOutOffset = dict["TempOutOffset"]
		meas.Weight = dict["Weight"]
		meas.WeightRaw = dict["WeightRaw"]
		meas.Status = DeviceStatus(dict["Status"])
		meas.Errors = [e for e in MeasurementError.__members__.values() if e.value&dict["Errors"]]
		return meas
	
	def dict(self):
		errors = 0
		for e in self.Errors:
			errors |= e.value
		return {
			"DateTime": self.DateTime.strftime("%Y-%m-%d %H:%M:%S"),
			"TempIn": self.TempIn,
			"TempInOffset": self.TempInOffset,
			"TempOut": self.TempOut,
			"TempOutOffset": self.TempOutOffset,
			"Weight": self.Weight,
			"WeightRaw": self.WeightRaw,
			"Status": self.Status.value,
			"Errors": errors
		}

class Device:
	def __init__(self, cfg):
		self.cfg = cfg
		
		self.motor = createMotor(self.cfg.motor.name, **self.cfg.motor.kwargs)
		self.tempRelayHeater = createTempRelay(self.cfg.tempRelayHeater.name, **self.cfg.tempRelayHeater.kwargs)
		self.tempSensorOut = createTempSensor(self.cfg.tempSensorOut.name, **self.cfg.tempSensorOut.kwargs)
		self.weightSensor = createWeightSensor(self.cfg.weightSensor.name, **self.cfg.weightSensor.kwargs)
		self.relayDeice = createRelay(self.cfg.relayDeice.name, **self.cfg.relayDeice.kwargs)
		
		self._lock = asyncio.Lock()
		self._status = DeviceStatus.MEASURE
	
	async def start(self):
		await self.tempRelayHeater.enable(self.cfg.sensor.temp.meas)
		await self.motor.run(self.cfg.sensor.rotRPM, dir=self.cfg.sensor.rotDir)
		await self.weightSensor.start()
	
	async def stop(self):
		await self.weightSensor.stop()
		await self.motor.stop()
	
	async def status(self):
		async with self._lock:
			return self._status
	
	async def read(self):
		async with self._lock:
			meas = Measurement()
			meas.Status = self._status
			res = await asyncio.gather(
				self.tempRelayHeater.temp(),
				self.tempSensorOut.temp(),
				self.weightSensor.weight(),
				return_exceptions=True
			)
		
		if isinstance(res[0], Exception):
			meas.Errors.append(MeasurementError.TEMPIN)
		else:
			meas.TempIn = res[0][0]
			meas.TempInOffset = res[0][1]
		if isinstance(res[1], Exception):
			meas.Errors.append(MeasurementError.TEMPOUT)
		else:
			meas.TempOut = res[1][0]
			meas.TempOutOffset = res[1][1]
		if isinstance(res[2], Exception):
			meas.Errors.append(MeasurementError.WEIGHT)
		else:
			meas.Weight = res[2][0]
			meas.WeightRaw = res[2][1]
		
		if meas.Errors:
			logging.debug("Measurement failed: {}".format(meas.Errors))
		else:
			logging.debug("Measurement successful")
		return meas
	
	async def deice(self):
		async with self._lock:
			if self._status == DeviceStatus.DEICE:
				return
			self._status = DeviceStatus.DEICE
			logging.info("Status: DEICE")
		
		await self.tempRelayHeater.enable(self.cfg.sensor.temp.deice)
		await self.relayDeice.on()
		await asyncio.sleep(self.cfg.sensor.deiceTime)
		
		async with self._lock:
			await self.relayDeice.off()
			await self.tempRelayHeater.enable(self.cfg.sensor.temp.meas)
			self._status = DeviceStatus.MEASURE
			logging.info("Status: MEASURE")
