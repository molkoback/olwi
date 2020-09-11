class TempSensorException(Exception):
	pass

class TempSensor:
	async def temp(self) -> (float, float):
		raise NotImplementedError()

class DummyTempSensor(TempSensor):
	async def temp(self):
		return 20.0, 0.0

devices = {"dummy": DummyTempSensor}
try:
	from olwi.hw.xyt01 import XYT01
	devices["XYT01"] = XYT01
except:
	pass
try:
	from olwi.hw.dsx8 import DSx8
	devices["DSx8"] = DSx8
except:
	pass

def createTempSensor(name, **kwargs):
	if not name in devices:
		raise TempSensorException("Invalid TempSensor '{}'".format(name))
	return devices[name](**kwargs)
