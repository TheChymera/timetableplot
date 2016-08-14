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

def tryme(joins, cols, expression):
	joinclassobject = allowed_classes[expression[0]]
	if isinstance(expression[2],list):
		joins,cols,parentclassobject_,joinclassobject_,alias_,aliased_col_ = tryme(joins, cols, expression[2])
		parentclassobject = alias_
		rootclassname = expression[2][2]
		joinclassobject_name = rootclassname+"_"+expression[0]
	else:
		parentclassobject = allowed_classes[expression[2]]
		joinclassobject_name = expression[0]
		rootclassname = expression[2]
	alias = aliased(joinclassobject, name=joinclassobject_name)
	joins.append((alias,getattr(parentclassobject, expression[1])))
	for col_name, col in inspection.inspect(joinclassobject).columns.items():
		aliased_col = getattr(joinclassobject, col.key)
		cols.append(aliased_col.label("{}_{}_{}".format(rootclassname,expression[0],col_name)))
	return joins,cols,parentclassobject,joinclassobject,alias,aliased_col

def multi_plot(db_path, select, x_key, shade, saturate, padding=4, saturate_cmap="Pastel1_r", baseclass="", filters=[]):
	"""Plotting tool

	Mandatory Arguments:
	db_path -- path of db to query for data (can use tilde for home dir)
	category -- main category to plot on x axis (must be a class from the db)
	select -- list of lists which must be either 2 (for join) or 3 (for filter) elements long
	padding -- number of entries to padd timeplan with
	saturate_cmap -- string indicating the matplotlib cmap to use (http://matplotlib.org/examples/color/colormaps_reference.html)
	"""

	session, engine = loadSession(db_path)

	cols=[]
	joins=[]
	baseclassobject = allowed_classes[baseclass]
	for i in [[baseclass]] + select:
		joinclassobject = allowed_classes[i[0]]
		if  i == [baseclass] or len(i) <3:
			for col_name, col in inspection.inspect(joinclassobject).columns.items():
				aliased_col = getattr(joinclassobject, col.key)
				cols.append(aliased_col.label("{}_{}".format(i[0], col_name)))
		if i != [baseclass]:
			if len(i) == 1:
				joins.append((joinclassobject,))
			elif len(i) == 2:
				joins.append((joinclassobject,getattr(baseclassobject, i[1])))
			elif len(i) == 3:
				joins,cols,_,_,_,_ = tryme(joins,cols,i)



	sql_query = session.query(*cols).select_from(baseclassobject)
	for join in joins:
		sql_query = sql_query.outerjoin(*join)
	# sql_query = sql_query.outerjoin(TreatmentProtocol, aliased=True)

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
	# print reference_df.index
	print reference_df.columns
	# print set(reference_df[u'Cage_Treatment_end_date'])
	# return
	# print set(reference_df[u'CageStay_start_date'])
	# print reference_df[reference_df["Cage_id"] == 18]
	# return
	reference_df = reference_df.dropna(axis="columns", how="all") #remove empty columns

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

	# print set(reference_df["Cage_Treatment_start_date"])
	# print set(reference_df["Cage_Treatment_end_date"])
	print set(reference_df["Treatment_start_date"])
	print set(reference_df["Treatment_end_date"])
	print set(reference_df["Treatment_id"])
	# print set(reference_df["Cage_Treatment_id"])
	print set(reference_df["CageStay_Cage_id"])
	print set(reference_df["TreatmentProtocol_code"])
	print set(reference_df["Cage_TreatmentProtocol_code"])

	return

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
					print filtered_df.columns
					return
					print entry[key][0]
					try:
						print list(set(filtered_df[entry[key][1]]))[0]
						start = list(set(filtered_df[entry[key][1]]))[0]
					except IndexError:
						print "BLANK_________________"
						pass
					if len(entry[key]) == 3:
						print entry[key][2]
						end = list(set(filtered_df[entry[key][2]]))[0]
						print end
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
	# print(mydf)
	# print(set(mydf[(mydf["Animal_id"]==1) & (mydf["FMRIMeasurement_preparation_id"] == 11)]["FMRIMeasurement_date"]))
	session.close()
	engine.dispose()
def newtest(db_path):
	session, engine = loadSession(db_path)

	# sql_query = session.query(Animal.id.label("Animal_id")).select_from(Animal)
	CageTreatment = aliased(Treatment)
	CageTreatmentProtocol = aliased(TreatmentProtocol)
	sql_query = session.query(
							Animal.id.label("Animal_id"),
							Treatment.id.label("Treatment_id"),
							TreatmentProtocol.code.label("TreatmentProtocol_code"),
							CageStay.id.label("CageStay_id"),
							Cage.id.label("Cage_id"),
							CageTreatment.id.label("CageTreatment_id"),
							CageTreatmentProtocol.code.label("CageTreatmentProtocol_code"),
							)\
					.join(Animal.treatments)\
					.outerjoin(Treatment.protocol)\
					.join(Animal.cage_stays)\
					.join(Cage)\
					.join(CageTreatment, Cage.treatments)\
					.join(CageTreatmentProtocol, CageTreatment.protocol)\
					.filter(Animal.id == 43)
					# .join(Cagetreatments)\
					# .outerjoin(CageTreatment)\
					# .outerjoin(Cage.treatments)\
	# sql_query = session.query(Animal.id.label("Animal_id")).select_from(Animal).filter(Animal.id == 1)
	# sql_query = session.query(Animal).filter(Animal.id == 1)

	mystring = sql_query.statement
	reference_df = pd.read_sql_query(mystring,engine)
	# print reference_df.index
	print reference_df.columns
	# print reference_df["Cage_id"]
	# print reference_df[reference_df["Animal_id"]==43]
	print reference_df

	session.close()
	engine.dispose()

if __name__ == '__main__':
	# select = [["Animal","treatments"],["FMRIMeasurement"],["TreatmentProtocol"]]
	# select = [["Cage"],["FMRIMeasurement"],["TreatmentProtocol"],["Treatment","start_date","2016,4,25","2016,4,25,19,30"]]
	select = [
		["Treatment","treatments"],
		["TreatmentProtocol"],
		["FMRIMeasurement"],
		["CageStay","cage_stays"],
		["Cage","cage","CageStay"],
		["TreatmentProtocol","protocol",["Treatment","treatments","Cage"]],
		# ["TreatmentProtocol","protocol","Treatment"],
		]
	filters = [["Treatment","start_date","2016,4,25"]]
	# filters = [["Treatment","start_date","2016,4,25","2016,4,25,19,30"]]
	# select = [["Treatment","treatments"],["FMRIMeasurement"],["TreatmentProtocol"],["CageStay","cage_stays"],["Cage","cage","CageStay"]]
	baseclass = "Animal"
	# select = [["Animal","treatments"],["FMRIMeasurement"],["TreatmentProtocol"],["Cage"],["Treatment","start_date","2016,4,25","2016,4,25,19,30"]]
	# select = [["Animal","treatments"],["FMRIMeasurement"],["TreatmentProtocol"],["Cage","treatments"],["Treatment","start_date","2016,4,25","2016,4,25,19,30"]]
	saturate = [
		{"TreatmentProtocol_code":["cFluDW","Treatment_start_date","Treatment_end_date"]},
		# {"Treatment_TreatmentProtocol_code":["cFluDW","Cage_Treatment_start_date","Cage_Treatment_end_date"]},
		{"TreatmentProtocol_code":["aFluIV","Treatment_start_date"]},
		{"TreatmentProtocol_code":["aFluSC","Treatment_start_date"]}
		]
	# multi_plot("~/syncdata/meta.db", select, "Animal_id", shade=["FMRIMeasurement_date"], saturate=saturate, baseclass=baseclass, filters=filters)
	# plt.show()
	newtest("~/syncdata/meta.db")
	# test("~/meta.db")
