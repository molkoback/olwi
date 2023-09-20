from olwi import homedir, datadir

import yaml
import os
import shutil

defaultFile = os.path.join(datadir, "config", "olwi.yaml")

def createConfigFile(dst):
	os.makedirs(os.path.split(dst)[0], exist_ok=True)
	shutil.copy(defaultFile, dst)

class ConfigException(Exception):
	pass

class Config:
	def __init__(self):
		self.file = None
	
	@classmethod
	def fromfile(cls, file):
		cfg = cls()
		cfg.read(file)
		return cfg
	
	@classmethod
	def fromtext(cls, text):
		cfg = cls()
		cfg.load(text)
		return cfg
	
	def read(self, file):
		self.file = file
		with open(file, "r") as fp:
			self.load(fp.read())
	
	def load(self, text):
		try:
			self.setDict(yaml.load(text, Loader=yaml.Loader))
		except Exception as e:
			raise ConfigException("Could not parse config:\n{}".format(e))
	
	def write(self, fn):
		with open(fn, "w") as fp:
			yaml.dump(self.dict, fp, Dumper=yaml.Dumper)
	
	def setDict(self, dict):
		self.dict = dict
		self.sensor = type("SensorParam", (object,), {
			"name": dict["sensor"]["name"],
			"measInterval": float(dict["sensor"]["meas_interval"]),
			"rotDir": bool(dict["sensor"]["rotation_dir"]),
			"rotRPM": float(dict["sensor"]["rotation_rpm"]),
			"temp": type("TempParam", (object,), {
				"meas": float(dict["sensor"]["temp"]["meas"]),
				"deice": float(dict["sensor"]["temp"]["deice"])
			}),
			"deiceTime": float(dict["sensor"]["deice_time"]),
			"maxWeight": float(dict["sensor"]["max_weight"])
		})
		self.web = type("WebServerParam", (object,), {
			"host": dict["web"]["host"],
			"port": int(dict["web"]["port"]),
			"url": dict["web"]["url"]
		})
		self.web.url = self.web.url if self.web.url.endswith("/") else self.web.url+"/"
		self.storage = type("StorageParam", (object,), {
			"size": int(dict["storage"]["size"]),
			"temporary": dict["storage"]["temporary"]
		})
		self.sql = type("SQLParam", (object,), {
			"host": dict["sql"]["host"],
			"port": int(dict["sql"]["port"]),
			"user": dict["sql"]["user"],
			"passwd": dict["sql"]["passwd"],
			"database": dict["sql"]["database"],
			"table": dict["sql"]["table"]
		})
		self.motor = self._creatable(dict["motor"], "MotorParam")
		self.tempRelayHeater = self._creatable(dict["temp_relay_heater"], "TempRelayParam")
		self.tempSensorOut = self._creatable(dict["temp_sensor_out"], "TempSensorParam")
		self.weightSensor = self._creatable(dict["weight_sensor"], "WeightSensorParam")
		self.relayDeice = self._creatable(dict["relay_deice"], "RelayParam")
	
	def _creatable(self, obj, clsname):
		k = next(iter(obj))
		return type(clsname, (object,), {
			"name": k,
			"kwargs": obj[k]
		})
