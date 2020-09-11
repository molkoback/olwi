from olwi import version

from setuptools import setup, find_packages

with open("README.md") as fp:
	readme = fp.read()

with open("requirements.txt") as fp:
	requirements = fp.read().splitlines()

setup(
	name="olwi",
	version=version,
	packages=find_packages(),
	
	install_requires=requirements,
	extras_require={
		"ads1115": ["adafruit-circuitpython-ads1x15>=2.2.2"],
		"gpiorelay": ["gpiozero>=1.5.0"],
		"pd1070": ["gpiozero>=1.5.0", "pyserial>=3.4"],
		"dsx8": ["w1thermsensor>=1.3.0"],
		"xyt01": ["pyserial>=3.4"]
	},
	
	package_data={"olwi": ["data/*"]},
	
	author="Eero Molkoselkä",
	author_email="eero.molkoselka@gmail.com",
	description="ISO 12494 standard based ice load instrument software.",
	long_description=readme,
	url="https://github.com/molkoback/olwi",
	license="MIT",
	
	entry_points={
		"console_scripts": [
			"olwi = olwi.ui.cli:main"
		]
	},
	
	classifiers=[
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3.5",
		"Topic :: Scientific/Engineering :: Atmospheric Science",
		"Topic :: Software Development :: Embedded Systems"
	]
)
