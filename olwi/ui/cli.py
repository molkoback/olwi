from olwi import version, homedir
from olwi.config import Config, createConfigFile
from olwi.controller import WebController

import argparse
import asyncio
import logging
import os
import sys

_versionMsg = """OLWI {version}

Copyright (C) 2020 Eero Molkoselkä <eero.molkoselka@gmail.com>
""".format(version=version)

def _parseArgs():
	parser = argparse.ArgumentParser("OLWI")
	parser.add_argument("cfg", nargs="?", default=None, help="config file", metavar="str")
	parser.add_argument("-d", "--debug", action="store_true", help="enable debug messages")
	parser.add_argument("-V", "--version", action="store_true", help="print version information")
	return parser.parse_args()

def _initLogging(level):
	root = logging.getLogger()
	root.setLevel(level)
	ch = logging.StreamHandler(sys.stdout)
	ch.setLevel(level)
	if level == logging.DEBUG:
		fmt = "[%(asctime)s]<%(module)s:%(lineno)d>(%(levelname)s) %(message)s"
	else:
		fmt = "[%(asctime)s](%(levelname)s) %(message)s"
	formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")
	ch.setFormatter(formatter)
	root.addHandler(ch)

def main():
	args = _parseArgs()
	if args.version:
		sys.stdout.write(_versionMsg)
		sys.exit(0)
	_initLogging(logging.DEBUG if args.debug else logging.INFO)
	
	try:
		if not args.cfg:
			args.cfg = os.path.join(homedir, "olwi.yaml")
		if not os.path.exists(args.cfg):
			createConfigFile(args.cfg)
		cfg = Config.fromfile(args.cfg)
		
		ctrl = WebController()
		loop = asyncio.get_event_loop()
		loop.create_task(ctrl.start(cfg))
		loop.run_forever()
	
	except KeyboardInterrupt:
		logging.info("Exiting")
