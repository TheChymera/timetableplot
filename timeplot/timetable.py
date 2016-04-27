#!/usr/bin/python
import datetime
import argh
import json
import sys
from datetime import *

from timeplan import add_grey
import matplotlib.cm as cm

from matplotlib.ticker import MultipleLocator, LinearLocator
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import matplotlib.ticker as ticker

import numpy as np
import matplotlib.pyplot as plt

import pandas as pd

from sqlalchemy import create_engine, literal, or_, inspection
from os import path
sys.path.append('/home/chymera/src/labbookdb/db/')
from query import get_related_id, instructions
from common_classes import *
from sqlalchemy.orm import sessionmaker, aliased
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

def multi_plot(db_path, select, x_key, shade, saturate, padding=4):
	"""Plotting tool

	Mandatory Arguments:
	db_path -- path of db to query for data (can use tilde for home dir)
	category -- main category to plot on x axis (must be a class from the db)
	select -- list of lists which must be either 2 (for join) or 3 (for filter) elements long
	padding -- number of entries to padd timeplan with
	"""

	session, engine = loadSession(db_path)

	cols=[]
	joins=[]
	filters=[]
	for i in select:
		for col_name, col in inspection.inspect(allowed_classes[i[0]]).columns.items():
			aliased_col = getattr(allowed_classes[i[0]], col.key)
			cols.append(aliased_col.label("{}_{}".format(i[0], col_name)))
		if 0 < len(i) <= 2:
			joins.append(i)
		elif 2 < len(i):
			filters.append(i)

	sql_query = session.query(*cols)
	for join in joins:
		if len(join) == 1:
			sql_query = sql_query.join(allowed_classes[join[0]])
		else:
			sql_query = sql_query.join(getattr(allowed_classes[join[0]], join[1]))

	for sub_filter in filters:
		if sub_filter[1][-4:] == "date" and isinstance(sub_filter[2], str):
			for ix, i in enumerate(sub_filter[2:]):
				sub_filter[2+ix] = datetime(*[int(a) for a in i.split(",")])
		if len(i) == 3:
			sql_query = sql_query.filter(getattr(allowed_classes[sub_filter[0]], sub_filter[1]) == sub_filter[2])
		else:
			sql_query = sql_query.filter(or_(getattr(allowed_classes[sub_filter[0]], sub_filter[1]) == v for v in sub_filter[2:]))

	mystring = sql_query.statement
	reference_df = pd.read_sql_query(mystring,engine)

	#truncate dates
	for col in reference_df.columns:
		if "date" in col:
			reference_df[col] = reference_df[col].apply(lambda x: x.date())


	#GET FIRST AND LAST DATE
	dates = get_dates(reference_df, [shade, saturate])
	window_start = min(dates) - timedelta(days=padding)
	window_end = max(dates) + timedelta(days=padding)

	#create generic plotting dataframe
	x_vals = list(set(reference_df[x_key]))
	datetime_index = [i for i in perdelta(window_start,window_end,timedelta(days=1))]

	df = pd.DataFrame(index=datetime_index, columns=x_vals)
	df = df.fillna(0)

	#set plotting params
	cMap = add_grey(cm.viridis, 0.9)
	fig, ax = plt.subplots(figsize=df.shape , facecolor='#eeeeee', tight_layout=True)

	#populate frames
	for entry in shade:
		df_ = df.copy(deep=True)
		for x_val in x_vals:
			if isinstance(entry, dict):
				for key in entry:
					filtered_df = reference_df[(reference_df[key] == entry[key][0])&(reference_df[x_key] == x_val)]
					start = list(set(filtered_df[entry[key][1]]))[0]
					if len(entry[key]) == 3:
						end = list(set(filtered_df[entry[key][2]]))[0]
						active_dates = [i for i in perdelta(start,end+timedelta(days=1),timedelta(days=1))]
						df_.set_value(active_dates, x_val, 1)
					else:
						df_.set_value(start, x_val, 1)
		print df_
		# plt.pcolor(df_)
		im = ax.pcolorfast(df_.T, cmap=add_grey(cm.gray_r, 0.8), alpha=.5)
		plt.hold(True)

	#populate frames
	for entry in saturate:
		df_ = df.copy(deep=True)
		for x_val in x_vals:
			if isinstance(entry, dict):
				for key in entry:
					filtered_df = reference_df[(reference_df[key] == entry[key][0])&(reference_df[x_key] == x_val)]
					start = list(set(filtered_df[entry[key][1]]))[0]
					print start
					if len(entry[key]) == 3:
						end = list(set(filtered_df[entry[key][2]]))[0]
						active_dates = [i for i in perdelta(start,end,timedelta(days=1))]
						df_.set_value(active_dates, x_val, 5)
						print end
					else:
						df_.set_value(start, x_val, 1)
			elif isinstance(entry, str):
				filtered_df = reference_df[reference_df[x_key] == x_val]
				active_dates = list(set(filtered_df[entry]))
				df_.set_value(active_dates, x_val, 1)
		# print df_
		# plt.pcolor(df_)
		im = ax.pcolorfast(df_.T, cmap=cm.PuRd, alpha=.5)
		plt.hold(True)

	#place and null major ticks (we still need them for the grid)
	ax.xaxis.set_major_locator(LinearLocator(len(df_.index)+1))
	ax.xaxis.set_major_formatter(ticker.NullFormatter())
	ax.yaxis.set_major_locator(LinearLocator(len(df_.columns)+1))
	ax.yaxis.set_major_formatter(ticker.NullFormatter())

	#place and format minor ticks (used to substitute for centered major tick labels)
	ax.xaxis.set_minor_locator(ticker.IndexLocator(1,0.5))
	ax.xaxis.set_minor_formatter(ticker.FixedFormatter(df_.index))
	ax.yaxis.set_minor_locator(ticker.IndexLocator(1,0.5))
	ax.yaxis.set_minor_formatter(ticker.FixedFormatter(df_.columns))

	#remove all major tick lines
	# plt.setp(ax.get_xticklines(),visible=False)

	#remove bottom and top small tick lines
	plt.tick_params(axis='x', which='both', bottom='off', top='off', left='off', right='off')
	plt.tick_params(axis='y', which='both', bottom='off', top='off', left='off', right='off')

	#Set only 7th minor tick label to visible
	for label in ax.xaxis.get_minorticklabels():
		label.set_visible(False)
	for label in ax.xaxis.get_minorticklabels()[::7]:
		label.set_visible(True)
	for label in ax.yaxis.get_minorticklabels():
		label.set_visible(False)
	for label in ax.yaxis.get_minorticklabels():
		label.set_visible(True)

	#Rotate ytick labels
	plt.setp(ax.xaxis.get_minorticklabels(), rotation=90)

	# create grid
	ax.xaxis.grid(True, which='major', color='1', linestyle='-')
	ax.yaxis.grid(True, which='major', color='1', linestyle='-')

	#delete all spines
	for spine in ["right", "left", "top", "bottom"]:
		ax.spines[spine].set_visible(False)

	plt.ylabel(" ".join(x_key.split("_")).replace("id","ID"))

	session.close()
	engine.dispose()

def perdelta(start, end, delta):
	curr = start
	while curr < end:
		yield curr
		curr += delta
	return

def get_dates(df, parameters):
	dates=[]
	for parameter in parameters:
		for entry in parameter:
			if isinstance(entry, str):
				dates.extend(list(set(df[entry])))
			if isinstance(entry, dict):
				for key in entry:
					filtered_df = df[df[key] == entry[key][0]]
					for col in entry[key][1:]:
						dates.extend(list(set(filtered_df[col])))
	return list(set(dates))

def test(db_path):
	session, engine = loadSession(db_path)

	cols=[]
	for category in ["Animal","Treatment","FMRIMeasurement"]:
		for col_name, col in inspection.inspect(allowed_classes[category]).columns.items():
			aliased_col = getattr(allowed_classes[category], col.key)
			cols.append(aliased_col.label("{}_{}".format(category, col_name)))

	sql_query = session.query(*cols).join(Animal.treatments).join(FMRIMeasurement).filter(or_(Treatment.start_date == v for v in [datetime(2015,11,10),datetime(2015,11,11)]))
	mystring = sql_query.statement
	mydf = pd.read_sql_query(mystring,engine)
	print(mydf)
	# print(set(mydf[(mydf["Animal_id"]==1) & (mydf["FMRIMeasurement_preparation_id"] == 11)]["FMRIMeasurement_date"]))
	session.close()
	engine.dispose()

if __name__ == '__main__':
	# argh.dispatch_command(add_generic)
	select = [["Animal","treatments"],["FMRIMeasurement"],["TreatmentProtocol"],["Treatment","start_date","2015,11,11","2015,11,10"]]
	shade = [{"TreatmentProtocol_code":["chrFlu","Treatment_start_date","Treatment_end_date"]},{"TreatmentProtocol_code":["acFlu","Treatment_start_date"]}]
	multi_plot("~/meta.db", select, "Animal_id", shade=shade, saturate=["FMRIMeasurement_date"])
	plt.show()
	# simple_query("~/meta.db", "FMRIMeasurement", [{"animal_id":"Animal:id_eth.4011"},{"animal_id":"Animal:id_eth.4009"}])
	# add_animal("~/animal.db", 4011, 4, "f", "2L", id_uzh="M2760", cage_uzh="570971")
	# test("~/meta.db")