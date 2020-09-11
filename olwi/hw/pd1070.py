from olwi.motor import Motor, MotorException

import asyncio
import gpiozero
import math
import serial
import struct

TMCL_SAP = 5
TMCL_GAP = 6
TMCL_STAP = 7
TMCL_RSAP = 8
TMCL_GIO = 15

TMCL_STATUS = {
	1: "Wrong checksum",
	2: "Invalid command",
	3: "Wrong type",
	4: "Invalid value",
	5: "Configuration EEPROM locked",
	6: "Command not available",
	100: "Successfully executed, no error",
	101: "Command loaded into TMCL program EEPROM"
}

class TMCL:
	def __init__(self, port):
		self.port = port
		self.addr = 1
		self._ser = None
	
	def __enter__(self):
		self.open()
		return self
	
	def __exit__(self, type, value, traceback):
		self.close()
	
	def open(self):
		self._ser = serial.Serial()
		self._ser.port = self.port
		self._ser.baudrate = 9600
		self._ser.parity = serial.PARITY_NONE
		self._ser.bytesize = serial.EIGHTBITS
		self._ser.stopbits = serial.STOPBITS_ONE
		self._ser.timeout = 2.0
		self._ser.open()
	
	def close(self):
		if self._ser is not None:
			self._ser.close()
	
	def _checksum(self, data):
		return sum([c for c in data]) & 255
	
	def read(self):
		data = self._ser.read(9)
		reply_addr, module_addr, status, cmd, val, checksum = struct.unpack(">BBBBiB", data)
		if not checksum == self._checksum(data[:-1]):
			status = 1
		if status < 100:
			raise MotorException("TMCL: {}".format(TMCL_STATUS[status]))
		return reply_addr, module_addr, status, cmd, val
	
	def write(self, cmd, type, bank, val):
		data = struct.pack(">BBBBi", self.addr, cmd, type, bank, val)
		checksum = self._checksum(data)
		data += bytes([checksum])
		self._ser.write(data)
		self._ser.flush()
	
	def send(self, cmd, type=0, bank=0, val=0):
		self.write(cmd, type, bank, val)
		return self.read()

class PD1070(Motor):
	def __init__(self, pins=[0, 0, 0, 0], port=None, resol=1, cogfact=1.0):
		self.en = None
		self.step = None
		self.chop = None
		self.dir = None
		self.en = gpiozero.DigitalOutputDevice(pins[0], initial_value=True)
		self.step = gpiozero.PWMOutputDevice(pins[1], initial_value=0)
		self.chop = gpiozero.DigitalOutputDevice(pins[2], initial_value=True)
		self.dir = gpiozero.DigitalOutputDevice(pins[3], initial_value=False)
		self.resol = resol
		self.cogfact = cogfact
		self.pulse = 3e-6
		
		self.port = port
		if self.port:
			self._setup()
	
	def _setup(self):
		with TMCL(self.port) as tmcl:
			# Step size 0-8
			val = int(math.log2(self.resol))
			tmcl.send(TMCL_SAP, type=140, bank=0, val=val)
			
			# Max current 0-31
			tmcl.send(TMCL_SAP, type=6, bank=0, val=8)
	
	def __del__(self):
		if self.en is not None:
			self.en.close()
		if self.step is not None:
			self.step.close()
		if self.chop is not None:
			self.chop.close()
		if self.dir is not None:
			self.dir.close()
	
	async def run(self, rpm, dir=True):
		if dir:
			self.dir.off()
		else:
			self.dir.on()
		
		steps = 200
		freq = self.cogfact * rpm / 60 * steps * self.resol
		self.step.frequency = freq
		self.step.value = self.pulse / (1/freq)
		self.en.off()
	
	async def stop(self):
		self.en.on()
		self.step.value = 0 
