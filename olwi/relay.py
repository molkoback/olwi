class RelayException(Exception):
	pass

class Relay:
	async def on(self) -> None:
		raise NotImplementedError()
	
	async def off(self) -> None:
		raise NotImplementedError()

class DummyRelay(Relay):
	async def on(self):
		pass
	
	async def off(self):
		pass

devices = {"dummy": DummyRelay}
try:
	from olwi.hw.gpiorelay import GPIORelay
	devices["GPIORelay"] = GPIORelay
except:
	pass

def createRelay(name, **kwargs):
	if not name in devices:
		raise RelayException("Invalid Relay '{}'".format(name))
	return devices[name](**kwargs)
