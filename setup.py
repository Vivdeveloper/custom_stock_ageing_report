from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in custom_stock_ageing_report/__init__.py
from custom_stock_ageing_report import __version__ as version

setup(
	name="custom_stock_ageing_report",
	version=version,
	description="custom_stock_ageing_report",
	author="sushant",
	author_email="sushantmanjare33@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
