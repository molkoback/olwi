from olwi.relay import Relay, RelayException

import gpiozero

class GPIORelay(Relay):
	def __init__(self, pin=0):
		self.pin = gpiozero.DigitalOutputDevice(pin, initial_value=False)
	
	async def on(self):
		self.pin.on()
	
	async def off(self):
		self.pin.off()
