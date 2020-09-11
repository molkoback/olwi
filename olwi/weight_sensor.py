class WeightSensorException(Exception):
	pass

class WeightSensor:
	async def reset(self) -> None:
		raise NotImplementedError()
	
	async def start(self, delay: float = 0) -> None:
		raise NotImplementedError()
	
	async def stop(self) -> None:
		raise NotImplementedError()
	
	async def reset(self) -> None:
		raise NotImplementedError()
	
	async def weight(self, avg: bool = True) -> (float, float):
		raise NotImplementedError()

class DummyWeightSensor:
	async def reset(self):
		pass
	
	async def start(self, delay=0):
		pass
	
	async def stop(self):
		pass
	
	async def reset(self):
		pass
	
	async def weight(self, avg=True):
		return 100.0, 0.0

devices = {"dummy": DummyWeightSensor}
try:
	from olwi.hw.ads1115 import ADS1115
	devices["ADS1115"] = ADS1115
except:
	pass

def createWeightSensor(name, **kwargs):
	if not name in devices:
		raise WeightSensorException("Invalid WeightSensor '{}'".format(name))
	return devices[name](**kwargs)
