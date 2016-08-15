#!/usr/bin/python
import datetime
import argh
import json
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from datetime import *

from plotting import ttp_style, add_grey
from os import path
import sqlalchemy
from sqlalchemy import create_engine, literal, or_, inspection
from sqlalchemy.orm import sessionmaker, aliased

sys.path.append(path.expanduser('~/src/LabbookDB/db/'))
from common_classes import *
from query import loadSession, allowed_classes

# def tryme(joins, cols, expression):
# 	joinclassobject = allowed_classes[expression[0]]
# 	if isinstance(expression[2],list):
# 		joins,cols,parentclassobject_,joinclassobject_,alias_,aliased_col_ = tryme(joins, cols, expression[2])
# 		parentclassobject = alias_
# 		rootclassname = expression[2][2]
# 		joinclassobject_name = rootclassname+"_"+expression[0]
# 	else:
# 		parentclassobject = allowed_classes[expression[2]]
# 		joinclassobject_name = expression[0]
# 		rootclassname = expression[2]
# 	alias = aliased(joinclassobject, name=joinclassobject_name)
# 	joins.append((alias,getattr(parentclassobject, expression[1])))
# 	for col_name, col in inspection.inspect(joinclassobject).columns.items():
# 		aliased_col = getattr(joinclassobject, col.key)
# 		cols.append(aliased_col.label("{}_{}_{}".format(rootclassname,expression[0],col_name)))
# 	return joins,cols,parentclassobject,joinclassobject,alias,aliased_col

def multi_plot(reference_df, x_key, shade, saturate, padding=4, saturate_cmap="Pastel1_r"):
	"""Plotting tool

	Mandatory Arguments:
	db_path -- path of db to query for data (can use tilde for home dir)
	category -- main category to plot on x axis (must be a class from the db)
	select -- list of lists which must be either 2 (for join) or 3 (for filter) elements long
	padding -- number of entries to padd timeplan with
	saturate_cmap -- string indicating the matplotlib cmap to use (http://matplotlib.org/examples/color/colormaps_reference.html)
	"""

	#truncate dates
	for col in reference_df.columns:
		if "date" in col:
			#the following catches None entries:
			try:
				reference_df[col] = reference_df[col].apply(lambda x: x.date())
			except AttributeError:
				pass


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
	df_ = df.copy(deep=True)
	for c_step, entry in enumerate(shade):
		for x_val in x_vals:
			if isinstance(entry, dict):
				for key in entry:
					start=False #unless the code below is succesful, no attempt is made to add an entry for the x_val
					filtered_df = reference_df[(reference_df[key] == entry[key][0])&(reference_df[x_key] == x_val)]
					try:
						start = list(set(filtered_df[entry[key][1]]))[0]
					except IndexError:
						pass
					if len(entry[key]) == 3:
						end = list(set(filtered_df[entry[key][2]]))[0]
						active_dates = [i for i in perdelta(start,end+timedelta(days=1),timedelta(days=1))]
						for active_date in active_dates:
							df_.set_value(active_date, x_val, df_.get_value(active_date, x_val)+c_step+1)
					elif start:
						df_.set_value(start, x_val, df_.get_value(start, x_val)+c_step+1)
			elif isinstance(entry, str):
				filtered_df = reference_df[reference_df[x_key] == x_val]
				active_dates = list(set(filtered_df[entry]))
				for active_date in active_dates:
					df_.set_value(active_date, x_val, df_.get_value(active_date, x_val)+c_step+1)
	im = ax.pcolorfast(df_.T, cmap=add_grey(cm.gray_r, 0.8), alpha=.5)
	plt.hold(True)

	#populate frames
	df_ = df.copy(deep=True)
	for c_step, entry in enumerate(saturate):
		for x_val in x_vals:
			if isinstance(entry, dict):
				for key in entry:
					filtered_df = reference_df[(reference_df[key] == entry[key][0])&(reference_df[x_key] == x_val)]
					try:
						start = list(set(filtered_df[entry[key][1]]))[0]
					except IndexError:
						pass
					if len(entry[key]) == 3:
						end = list(set(filtered_df[entry[key][2]]))[0]
						active_dates = [i for i in perdelta(start,end+timedelta(days=1),timedelta(days=1))]
						for active_date in active_dates:
							df_.set_value(active_date, x_val, df_.get_value(active_date, x_val)+c_step+1)
					elif start:
						df_.set_value(start, x_val, df_.get_value(start, x_val)+c_step+1)
					# we need this to make sure start does not remain set for the next iteration:
					start=False
			elif isinstance(entry, str):
				filtered_df = reference_df[reference_df[x_key] == x_val]
				active_dates = list(set(filtered_df[entry]))
				df_.set_value(active_dates, x_val, 1)
	# print(df_[20:])
	im = ax.pcolorfast(df_.T, cmap=add_grey(getattr(cm,saturate_cmap), 0.9), alpha=.5)
	plt.hold(True)

	ax = ttp_style(ax, df_)

	plt.ylabel(" ".join(x_key.split("_")).replace("id","ID"))

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

def add_all_columns(cols, class_name):
	joinclassobject = allowed_classes[class_name]

	#we need to catch this esception, because for aliased classes a mapper is not directly returned
	try:
		col_name_cols = inspection.inspect(joinclassobject).columns.items()
	except AttributeError:
		col_name_cols = inspection.inspect(joinclassobject).mapper.columns.items()

	for col_name, col in col_name_cols:
		column = getattr(joinclassobject, col.key)
		cols.append(column.label("{}_{}".format(class_name, col_name)))

def get_referece_df(db_path, col_entries=[], join_entries=[], filters=[]):
	session, engine = loadSession(db_path)

	cols=[]
	for col_entry in col_entries:
		if len(col_entry) == 1:
			add_all_columns(cols, col_entry[0])
		if len(col_entry) == 2:
			cols.append(getattr(allowed_classes[col_entry[0]],col_entry[1]).label("{}_{}".format(*col_entry)))
		if len(col_entry) == 3:
			aliased_class = aliased(allowed_classes[col_entry[1]])
			allowed_classes[col_entry[0]+"_"+col_entry[1]] = aliased_class
			if col_entry[2] == "":
				add_all_columns(cols, col_entry[0]+"_"+col_entry[1])
			else:
				cols.append(getattr(aliased_class,col_entry[2]).label("{}_{}_{}".format(*col_entry)))

	joins=[]
	for join_entry in join_entries:
		join_parameters = []
		for join_entry_substring in join_entry:
			if "." in join_entry_substring:
				class_name, table_name = join_entry_substring.split(".") #if this unpacks >2 values, the user specified strings are malformed
				join_parameters.append(getattr(allowed_classes[class_name],table_name))
			else:
				join_parameters.append(allowed_classes[join_entry_substring])
		joins.append(join_parameters)

	sql_query = session.query(*cols)
	for join in joins:
		sql_query = sql_query.join(*join)

	for sub_filter in filters:
		if sub_filter[1][-4:] == "date" and isinstance(sub_filter[2], str):
			for ix, i in enumerate(sub_filter[2:]):
				sub_filter[2+ix] = datetime(*[int(a) for a in i.split(",")])
		if len(sub_filter) == 3:
			sql_query = sql_query.filter(getattr(allowed_classes[sub_filter[0]], sub_filter[1]) == sub_filter[2])
		else:
			sql_query = sql_query.filter(or_(getattr(allowed_classes[sub_filter[0]], sub_filter[1]) == v for v in sub_filter[2:]))

	mystring = sql_query.statement
	df = pd.read_sql_query(mystring,engine)
	session.close()
	engine.dispose()

	return df

	#THIS IS KEPT TO REMEMBER WHENCE THE ABOVE AWKWARD ROUTINES CAME AND HOW THE CODE IS SUPPOSED TO LOOK IF TYPED OUT
	# CageTreatment = aliased(Treatment)
	# CageTreatmentProtocol = aliased(TreatmentProtocol)
	# sql_query = session.query(
	# 						Animal.id.label("Animal_id"),
	# 						TreatmentProtocol.code.label("TreatmentProtocol_code"),
	# 						Cage.id.label("Cage_id"),
	# 						CageTreatment.id.label("Cage_Treatment_id"),
	# 						CageTreatmentProtocol.code.label("Cage_TreatmentProtocol_code"),
	# 						)\
	# 				.join(Animal.treatments)\
	# 				.join(Treatment.protocol)\
	# 				.join(Animal.cage_stays)\
	# 				.join(CageStay.cage)\
	# 				.join(CageTreatment, Cage.treatments)\
	# 				.join(CageTreatmentProtocol, CageTreatment.protocol)\
	# 				.filter(Animal.id == 43)
	# mystring = sql_query.statement
	# reference_df = pd.read_sql_query(mystring,engine)
	# print reference_df.columns
	# print reference_df

if __name__ == '__main__':
	saturate = [
		{"Cage_TreatmentProtocol_code":["cFluDW","Cage_Treatment_start_date","Cage_Treatment_end_date"]},
		# {"Treatment_TreatmentProtocol_code":["cFluDW","Cage_Treatment_start_date","Cage_Treatment_end_date"]},
		{"TreatmentProtocol_code":["aFluIV","Treatment_start_date"]},
		{"TreatmentProtocol_code":["aFluSC","Treatment_start_date"]}
		]

	col_entries=[("Animal","id"),("Treatment",),("FMRIMeasurement",),("TreatmentProtocol","code"),("Cage","id"),("Cage","Treatment",""),("Cage","TreatmentProtocol","code")]
	join_entries=[("Animal.treatments",),("FMRIMeasurement",),("Treatment.protocol",),("Animal.cage_stays",),("CageStay.cage",),("Cage_Treatment","Cage.treatments"),("Cage_TreatmentProtocol","Cage_Treatment.protocol")]
	filters = [["Cage_Treatment","start_date","2016,4,25,19,30"]]
	reference_df = get_referece_df("~/syncdata/meta.db",col_entries=col_entries, join_entries=join_entries, filters=filters)
	# print reference_df.columns

	multi_plot(reference_df, "Animal_id", shade=["FMRIMeasurement_date"], saturate=saturate)
	plt.show()
