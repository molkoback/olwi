from olwi.temp_sensor import TempSensor

from w1thermsensor import W1ThermSensor

class DSx8(TempSensor):
	def __init__(self, id=None, offset=0.0):
		self.id = id
		self.offset = offset
		self._sensor = W1ThermSensor(sensor_id=id)
	
	async def temp(self):
		return (self._sensor.get_temperature()) + self.offset, self.offset
