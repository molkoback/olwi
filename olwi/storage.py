from olwi import homedir
from olwi.device import Measurement

import asyncio
import logging
import os
import sqlite3

class StorageException(Exception):
	pass

class Storage:
	def __init__(self, cfg):
		self.size = cfg.storage.size
		self._list = []
		self._conn = None
		self._lock = asyncio.Lock()
		
		if not cfg.storage.temporary:
			self._createSQLite()
	
	def __del__(self):
		self.close()
	
	def close(self):
		if not self._conn is None:
			self._conn.close()
	
	def _dict_factory(self, curs, row):
		dict = {}
		for i, col in enumerate(curs.description):
			dict[col[0]] = row[i]
		return dict
	
	def _createSQLite(self):
		file = os.path.join(homedir, "olwi.db")
		if not os.path.exists(file):
			os.makedirs(os.path.dirname(file), exist_ok=True)
		self._conn = sqlite3.connect(file)
		self._conn.row_factory = self._dict_factory
		
		curs = self._conn.cursor()
		cmd = "CREATE TABLE IF NOT EXISTS measurements (ID INTEGER PRIMARY KEY, DateTime DATETIME(0), TempIn FLOAT, TempInOffset FLOAT, TempOut FLOAT, TempOutOffset FLOAT, Weight FLOAT, WeightRaw FLOAT, Status INTEGER, Errors INTEGER);"
		curs.execute(cmd)
		self._list = self._readSQLite(curs)
		self._conn.commit()
		curs.close()
		
		logging.debug("Local storage {}".format(file))
	
	def _readSQLite(self, curs):
		l = []
		cmd = "SELECT * FROM measurements ORDER BY DateTime DESC;"
		for row in curs.execute(cmd):
			l.append(Measurement.fromdict(row))
		return l
	
	def _putList(self, meas):
		if self.size > 0 and len(self._list) >= self.size:
			self._list.pop(-1)
		self._list.insert(0, meas)
	
	def _putSQLite(self, meas):
		meas = meas.dict()
		keys = meas.keys()
		values = tuple(meas.values())
		
		curs = self._conn.cursor()
		cmd = "INSERT INTO measurements (ID, {}) VALUES (NULL,{});".format(
			",".join(keys),
			",".join(["?" for k in keys])
		)
		curs.execute(cmd, values)
		
		if self.size > 0 and len(self._list) >= self.size:
			cmd = "DELETE FROM measurements WHERE DateTime = (SELECT MIN(DateTime) FROM measurements);"
			curs.execute(cmd)
		
		self._conn.commit()
		curs.close()
	
	async def put(self, meas):
		async with self._lock:
			self._putList(meas)
			if not self._conn is None:
				self._putSQLite(meas)
	
	async def read(self, n=-1, offset=0, order="desc"):
		if n < 0:
			n = self.size
		async with self._lock:
			if order == "desc":
				list = self._list[offset:offset+n]
			else:
				list = self._list[::-1]
				list = list[offset:offset+n]
		return list
