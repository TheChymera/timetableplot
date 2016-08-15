#!/usr/bin/python
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

sys.path.append(path.expanduser('~/src/LabbookDB/db/'))
from query import get_df

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

def multi_plot(reference_df, x_key, shade, saturate, padding=4, saturate_cmap="Pastel1_r", window_start="", window_end=""):
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
	if not window_start:
		window_start = min(dates) - timedelta(days=padding)
	else:
		window_start = datetime.strptime(window_start, "%Y,%m,%d").date()
	if not window_end:
		window_end = max(dates) + timedelta(days=padding)
	else:
		window_end = datetime.strptime(window_end, "%Y,%m,%d").date()

	# window_start = min(dates) - timedelta(days=padding)
	# window_end = max(dates) + timedelta(days=padding)

	#create generic plotting dataframe
	x_vals = list(set(reference_df[x_key]))
	datetime_index = [i for i in perdelta(window_start,window_end,timedelta(days=1))]

	df = pd.DataFrame(index=datetime_index, columns=x_vals)
	df = df.fillna(0)

	#set plotting params
	cMap = add_grey(cm.viridis, 0.9)
	fig_shape = (df.shape[0],df.shape[1]/1.5) #1.5 seems like a good scaling value to make cells not-too-tall and not-too-short
	fig, ax = plt.subplots(figsize=fig_shape , facecolor='#eeeeee', tight_layout=True)

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
					#escaping dates which are outside the date range (e.g. when specifying tighter window_end and window_start contraints)
					try:
						df_.set_value(active_date, x_val, df_.get_value(active_date, x_val)+c_step+1)
					except KeyError:
						pass
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

if __name__ == '__main__':
	saturate = [
		{"Cage_TreatmentProtocol_code":["cFluDW","Cage_Treatment_start_date","Cage_Treatment_end_date"]},
		{"TreatmentProtocol_code":["aFluIV","Treatment_start_date"]},
		{"TreatmentProtocol_code":["aFluSC","Treatment_start_date"]}
		]

	col_entries=[("Animal","id"),("Treatment",),("FMRIMeasurement",),("TreatmentProtocol","code"),("Cage","id"),("Cage","Treatment",""),("Cage","TreatmentProtocol","code")]
	join_entries=[("Animal.treatments",),("FMRIMeasurement",),("Treatment.protocol",),("Animal.cage_stays",),("CageStay.cage",),("Cage_Treatment","Cage.treatments"),("Cage_TreatmentProtocol","Cage_Treatment.protocol")]
	filters = [["Cage_Treatment","start_date","2016,4,25,19,30"]]
	reference_df = get_df("~/syncdata/meta.db",col_entries=col_entries, join_entries=join_entries, filters=filters)

	multi_plot(reference_df, "Animal_id", shade=["FMRIMeasurement_date"], saturate=saturate, window_end="2016,6,3")
	plt.show()
