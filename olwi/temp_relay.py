from olwi.temp_sensor import TempSensor

class TempRelayException(Exception):
	pass

class TempRelay(TempSensor):
	async def enable(self, thresh: float) -> None:
		raise NotImplementedError()
	
	async def disable(self) -> None:
		raise NotImplementedError()

class DummyTempRelay(TempRelay):
	async def temp(self):
		return 20.0, 0.0
	
	async def enable(self, thresh):
		pass
	
	async def disable(self):
		pass

devices = {"dummy": DummyTempRelay}
try:
	from olwi.hw.xyt01 import XYT01
	devices["XYT01"] = XYT01
except:
	pass

def createTempRelay(name, **kwargs):
	if not name in devices:
		raise TempRelayException("Invalid TempRelay '{}'".format(name))
	return devices[name](**kwargs)
