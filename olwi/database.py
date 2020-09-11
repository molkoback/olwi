import pymysql

from datetime import datetime
import logging
import warnings

class DatabaseException(Exception):
	pass

class Database:
	def __init__(self, cfg):
		self.cfg = cfg
		self._conn = None
		self._open()
	
	def _open(self):
		self._conn = pymysql.connect(
			host=self.cfg.sql.host,
			port=self.cfg.sql.port,
			user=self.cfg.sql.user,
			password=self.cfg.sql.passwd,
			cursorclass=pymysql.cursors.DictCursor
		)
		
		cmds = [
			"CREATE DATABASE IF NOT EXISTS {};".format(self.cfg.sql.database),
			"CREATE TABLE IF NOT EXISTS {}.{} (ID INT UNSIGNED NOT NULL AUTO_INCREMENT, DateTime DATETIME(0) NOT NULL, TempIn FLOAT NOT NULL, TempInOffset FLOAT NOT NULL, TempOut FLOAT NOT NULL, TempOutOffset FLOAT NOT NULL, Weight FLOAT NOT NULL, WeightRaw FLOAT NOT NULL, Status TINYINT UNSIGNED NOT NULL, Errors TINYINT UNSIGNED NOT NULL, PRIMARY KEY (ID));".format(self.cfg.sql.database, self.cfg.sql.table)
		]
		with self._conn.cursor() as curs:
			self._exec(curs, cmds)
		self._conn.commit()
		
		logging.info("SQL database {}:{}/{}.{}".format(self.cfg.sql.host, self.cfg.sql.port, self.cfg.sql.database, self.cfg.sql.table))
	
	def __del__(self):
		self.close()
	
	def close(self):
		if not self._conn is None:
			self._conn.close()
	
	def _exec(self, curs, cmds):
		for cmd in cmds:
			with warnings.catch_warnings():
				warnings.simplefilter("ignore")
				curs.execute(cmd)
	
	async def sync(self, storage):
		cmd = "SELECT DateTime from {}.{} ORDER BY DateTime DESC LIMIT 1".format(self.cfg.sql.database, self.cfg.sql.table)
		with self._conn.cursor() as curs:
			self._exec(curs, [cmd])
			res = curs.fetchone()
			if res is not None:
				dt = res["DateTime"]
			else:
				dt = datetime.fromtimestamp(0)
		
		for meas in await storage.read(order="asc"):
			if meas.DateTime > dt:
				await self.insert(meas)
	
	async def insert(self, meas):
		meas = meas.dict()
		keys = meas.keys()
		values = []
		for val in meas.values():
			if isinstance(val, float):
				values.append("{:16f}".format(val))
			elif isinstance(val, int):
				values.append(str(val))
			else:
				values.append("'{}'".format(val))
		
		cmd = "INSERT INTO {}.{} (ID,{}) VALUES (NULL,{});".format(
			self.cfg.sql.database, self.cfg.sql.table,
			",".join(keys),
			",".join(values)
		)
		with self._conn.cursor() as curs:
			self._exec(curs, [cmd])
		self._conn.commit()
