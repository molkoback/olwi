from olwi.temp_relay import TempRelay, TempRelayException

import serial

import asyncio
import time

class XYT01(TempRelay):
	def __init__(self, port="/dev/serial0", offset=0.0, thresh=5.0, hyst=1.0):
		self.port = port
		self.offset = offset
		self.thresh = thresh
		self.hyst = hyst
		
		self._loop = asyncio.get_event_loop()
		self._writeDelay = 0.5
		self._writeTime = 0
		
		self._ser = serial.Serial()
		self._ser.port = self.port
		self._ser.baudrate = 9600
		self._ser.bytesize = serial.EIGHTBITS
		self._ser.stopbits = serial.STOPBITS_ONE
		self._ser.timeout = 2.0
		self._ser.open()
		self._writeNow("start")
	
	def close(self):
		self._ser.close()
	
	def _read(self):
		if self._ser.in_waiting:
			data = self._ser.read(self._ser.in_waiting)
		else:
			data = self._ser.read_until(b"\r\n")
		data = data.decode("ascii", errors="ignore").strip("\x00\r\n")
		return data.split("\r\n")
	
	async def _aread(self):
		return await self._loop.run_in_executor(None, self._read)
	
	def _writeNow(self, line):
		self._writeTime = time.time()
		self._ser.write(line.encode("ascii"))
		self._ser.flush()
	
	async def _write(self, line):
		delta = time.time() - self._writeTime
		if delta < self._writeDelay:
			await asyncio.sleep(self._writeDelay - delta)
		self._writeNow(line)
	
	async def temp(self):
		line = (await self._aread())[-1]
		try:
			return float(line.split(",")[0]) + self.offset, self.offset
		except:
			raise TempRelayException("XYT01 returned an invalid value")
	
	async def _writeLines(self, lines):
		await self._write("stop")
		await asyncio.sleep(0.050)
		self._ser.reset_input_buffer()
		for line in lines:
			await self._write(line)
			await self._aread()
		await self._write("start")
	
	async def enable(self):
		if self.thresh >= -50.0 and self.thresh < 0.0:
			lineThresh = "S:{:03d}".format(int(self.thresh))
		elif self.thresh < 100.0:
			lineThresh = "S:{:04.1f}".format(self.thresh)
		elif self.thresh < 110.0:
			lineThresh = "S:{}".format(int(self.thresh))
		else:
			raise TempRelayException("Value out of range: {}".format(self.thresh))
		
		if self.hyst >= 0.0 and self.hyst <= 30.0:
			lineHyst = "B:{:04.1f}".format(self.hyst)
		else:
			raise TempRelayException("Value out of range: {}".format(self.hyst))
		
		await self._writeLines([lineThresh, lineHyst, "on"])
	
	async def disable(self):
		await self._writeLines(["off"])
