#!/usr/bin/python
import datetime
import argh
import json
import sys
from datetime import datetime

import pandas as pd

from sqlalchemy import create_engine, literal
from os import path
sys.path.append('/home/chymera/src/labbookdb/db/')
from query import get_related_id, instructions
from common_classes import *
from sqlalchemy.orm import sessionmaker
import sqlalchemy

allowed_classes = {
	"Animal": Animal,
	"Cage": Cage,
	"DNAExtractionProtocol": DNAExtractionProtocol,
	"FMRIMeasurement": FMRIMeasurement,
	"FMRIScannerSetup": FMRIScannerSetup,
	"FMRIAnimalPreparationProtocol": FMRIAnimalPreparationProtocol,
	"HandlingHabituationProtocol": HandlingHabituationProtocol,
	"Ingredient": Ingredient,
	"Incubation": Incubation,
	"MeasurementUnit": MeasurementUnit,
	"Operator": Operator,
	"Substance": Substance,
	"Solution": Solution,
	"Treatment":Treatment,
	"TreatmentProtocol":TreatmentProtocol,
	}

def simple_query(db_path, category, filters={}, mask=""):
	session, engine = loadSession(db_path)
	if isinstance(filters, list):
		df_list = []
		for subfilters in filters:
			sql_query=session.query(allowed_classes[category])
			for key in subfilters:
				if key[-3:] == "_id" and not isinstance(subfilters[key], int):
					try:
						input_values = get_related_id(session, engine, subfilters[key])
					except ValueError:
						instructions("table_identifier")
					for input_value in input_values:
						input_value = int(input_value)
						sql_query = sql_query.filter(getattr(allowed_classes[category], key)==input_value)
				else:
					sql_query = sql_query.filter(getattr(allowed_classes[category], key)==subfilters[key])
			mystring = sql_query.statement
			subdf = pd.read_sql_query(mystring,engine)
			df_list.append(subdf)
		mydf = pd.concat(df_list)
	if mask:
		mydf = mydf[mask]
	print(mydf)
	session.close()
	engine.dispose()

def loadSession(db_path):
	db_path = "sqlite:///" + path.expanduser(db_path)
	engine = create_engine(db_path, echo=False)
	Session = sessionmaker(bind=engine)
	session = Session()
	Base.metadata.create_all(engine)
	return session, engine

def multi_plot(db_path, category, bg_select={}, fg_select={}):
	"""Plotting tool

	Mandatory Arguments:
	db_path -- path of db to query for data (can use tilde for home dir)
	category -- main category to plot on x axis (must be a class from the db)
	bg_select -- list of lists which must be either 2 (for join) or 3 (for filter) elements long
	"""

	session, engine = loadSession(db_path)
	# sql_query = session.query(Animal).filter(Animal.treatments.any(start_date=datetime(2015,11,10))).filter(TreatmentProtocol.solution.has(code="fluIVP"))
	# sql_query = session.query(Animal).join(Animal.treatments).filter(Treatment.start_date == datetime(2015,11,10))

	sql_query = session.query(allowed_classes[category])
	bg_filters=[]
	for i in bg_select:
		if len(i) == 3:
			bg_filters.append(i)
		elif len(i) == 2:
			sql_query = sql_query.join(getattr(allowed_classes[i[0]], i[1]))
		else:
			print("WARNING: The bg_select entry you have provided: `"+i+"` is not appropriately formatted.")
	for i in bg_filters:
		sql_query = sql_query.filter(getattr(allowed_classes[i[0]], i[1]) == i[2])

	mystring = sql_query.statement
	mydf = pd.read_sql_query(mystring,engine)
	print(mydf)
	session.close()
	engine.dispose()

if __name__ == '__main__':
	# argh.dispatch_command(add_generic)
	multi_plot("~/meta.db", "Animal", [["Animal","treatments"],["Treatment","protocol"],["TreatmentProtocol","code","chrFlu"]])
	# simple_query("~/meta.db", "FMRIMeasurement", [{"animal_id":"Animal:id_eth.4011"},{"animal_id":"Animal:id_eth.4009"}])
	# add_animal("~/animal.db", 4011, 4, "f", "2L", id_uzh="M2760", cage_uzh="570971")
