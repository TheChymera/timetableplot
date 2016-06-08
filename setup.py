from setuptools import setup, find_packages

setup(
	name="timetableplot",
	version="",
	description = "Create overview figures of timetables",
	author = "Horea Christian",
	author_email = "h.chr@mail.ru",
	url = "https://github.com/TheChymera/timetableplot",
	keywords = ["plot", "schedule", "time", "timetable"],
	packages = find_packages("."),
	install_requires = [],
	provides = ["ttp"],
	)
