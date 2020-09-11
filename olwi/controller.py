from olwi import datadir
from olwi.config import Config, defaultFile
from olwi.database import Database
from olwi.device import Device
from olwi.hw.system import readSystemParam
from olwi.measure import Measure
from olwi.storage import Storage

import aiohttp
import aiohttp.web
import aiohttp_jinja2
import jinja2

import asyncio
import logging
import os

class WebController:
	def __init__(self):
		self.cfg = None
		
		self.device = None
		self.measure = None
		self.storage = None
		self.database = None
		
		self.app = None
		self.runner = None
		self.site = None
	
	async def _resp(self, resp):
		meas = await self.storage.read(n=1, offset=0)
		if meas:
			resp = {**meas[0].dict(), **resp}
		resp["databaseOk"] = self.database is not None
		return resp
	
	async def _apiResp(self, resp):
		return aiohttp.web.json_response(resp)
	
	@aiohttp_jinja2.template("index.htm")
	async def _handle_index(self, r):
		return await self._resp({})
	
	@aiohttp_jinja2.template("system.htm")
	async def _handle_system(self, r):
		return await self._resp(readSystemParam())
	
	@aiohttp_jinja2.template("settings.htm")
	async def _handle_settings(self, r):
		with open(self.cfg.file) as fp:
			configText = fp.read()
		with open(defaultFile) as fp:
			configTextDefault = fp.read()
		return await self._resp({
			"configText": configText,
			"configTextDefault": configTextDefault
		})
	
	@aiohttp_jinja2.template("help.htm")
	async def _handle_help(self, r):
		return await self._resp({})
	
	async def _handle_api(self, r):
		return await self._apiResp([meas.dict() for meas in await self.storage.read()])
	
	async def _handle_api_settings_check(self, r):
		resp = {"error": None}
		try:
			cfg = Config.fromtext((await r.post())["text"])
		except Exception as e:
			resp["error"] = str(e)
		return await self._apiResp(resp)
	
	async def _handle_api_settings_set(self, r):
		text = (await r.post())["text"]
		resp = {"error": None}
		try:
			cfg = Config.fromtext(text)
			with open(self.cfg.file, "w") as fp:
				fp.write(text)
			cfg.file = self.cfg.file
		except Exception as e:
			resp["error"] = str(e)
			return await self._apiResp(resp)
		
		asyncio.get_event_loop().create_task(self.restart(cfg, 5))
		return await self._apiResp(resp)
	
	async def startWebServer(self):
		host = self.cfg.web.host
		port = self.cfg.web.port
		url = self.cfg.web.url
		
		self.app = aiohttp.web.Application()
		aiohttp_jinja2.setup(self.app, loader=jinja2.FileSystemLoader(
			os.path.join(datadir, "templates")
		))
		self.app["static_root_url"] = url+"static"
		self.app.add_routes([
			aiohttp.web.static(self.app["static_root_url"], os.path.join(datadir, "static")),
			aiohttp.web.get(url, self._handle_index, name="index"),
			aiohttp.web.get(url+"system", self._handle_system, name="system"),
			aiohttp.web.get(url+"settings", self._handle_settings, name="settings"),
			aiohttp.web.get(url+"help", self._handle_help, name="help"),
			aiohttp.web.get(url+"api", self._handle_api, name="api"),
			aiohttp.web.post(url+"api/settings/check", self._handle_api_settings_check, name="api-settings-check"),
			aiohttp.web.post(url+"api/settings/set", self._handle_api_settings_set, name="api-settings-set")
		])
		
		self.runner = aiohttp.web.AppRunner(self.app)
		await self.runner.setup()
		self.site = aiohttp.web.TCPSite(self.runner, host, port)
		logging.info("Web server http://{}:{}{}".format(host, port, url))
		await self.site.start()
	
	async def stopWebServer(self):
		logging.info("Stopping web server")
		await self.app.shutdown()
		await self.app.cleanup()
		await self.site.stop()
		await self.runner.cleanup()
	
	async def startOLWI(self):
		logging.info("Sensor {}".format(self.cfg.sensor.name))
		
		self.device = Device(self.cfg)
		self.storage = Storage(self.cfg)
		try:
			self.database = Database(self.cfg)
		except Exception as e:
			self.database = None
			logging.info("No SQL database connection")
			logging.debug(str(e))
		self.measure = Measure(self.cfg, self.device, self.storage, self.database)
		
		await self.device.start()
		await self.measure.start()
	
	async def stopOLWI(self):
		logging.info("Stopping sensor")
		await self.measure.stop()
		await self.device.stop()
		self.database.close()
		self.storage.close()
	
	async def start(self, cfg):
		self.cfg = cfg
		await self.startOLWI()
		await self.startWebServer()
	
	async def stop(self):
		await self.stopOLWI()
		await self.stopWebServer()
	
	async def restart(self, cfg, delay=0):
		await asyncio.sleep(delay)
		await self.stop()
		asyncio.get_event_loop().create_task(self.start(cfg))
