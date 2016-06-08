from setuptools import setup, find_packages

setup(
	name="timeplot",
	version="",
	description = "Create overview figures of timetables",
	author = "Horea Christian",
	author_email = "h.chr@mail.ru",
	url = "https://github.com/TheChymera/timeplot",
	keywords = ["plot", "schedule", "time", "timetable"],
	packages = find_packages("."),
	install_requires = [],
	provides = ["ttp"],
	)
