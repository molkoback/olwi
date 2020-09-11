class MotorException(Exception):
	pass

class Motor:
	async def run(self, rpm: float, dir: bool = True) -> None:
		raise NotImplementedError()
	
	async def stop(self) -> None:
		raise NotImplementedError()

class DummyMotor(Motor):
	async def run(self, rpm, dir=True):
		pass
	
	async def stop(self):
		pass

devices = {"dummy": DummyMotor}
try:
	from olwi.hw.pd1070 import PD1070
	devices["PD1070"] = PD1070
except:
	pass

def createMotor(name, **kwargs):
	if not name in devices:
		raise MotorException("Invalid Motor '{}'".format(name))
	return devices[name](**kwargs)
