import matplotlib.pyplot as plt

from labbookdb.db.query import get_df

import timetable

def dwcohort1():
	saturate = [
		{"Cage_TreatmentProtocol_code":["cFluDW","Cage_Treatment_start_date","Cage_Treatment_end_date"]},
		{"TreatmentProtocol_code":["aFluIV","Treatment_start_date"]},
		{"TreatmentProtocol_code":["aFluSC","Treatment_start_date"]}
		]

	col_entries=[("Animal","id"),("Treatment",),("FMRIMeasurement",),("TreatmentProtocol","code"),("Cage","id"),("Cage","Treatment",""),("Cage","TreatmentProtocol","code")]
	join_entries=[("Animal.treatments",),("FMRIMeasurement",),("Treatment.protocol",),("Animal.cage_stays",),("CageStay.cage",),("Cage_Treatment","Cage.treatments"),("Cage_TreatmentProtocol","Cage_Treatment.protocol")]
	filters = [["Cage_Treatment","start_date","2016,4,25,19,30"]]

	# setting outerjoin to true will indirectly include controls
	reference_df = get_df("~/syncdata/meta.db",col_entries=col_entries, join_entries=join_entries, filters=filters, outerjoin=True)

	timetable.multi_plot(reference_df, "Animal_id", shade=["FMRIMeasurement_date"], saturate=saturate, window_end="2016,6,2")
	# multi_plot(reference_df, "Animal_id", shade=["FMRIMeasurement_date"], saturate=saturate, window_end="2016,6,3")
	plt.show()

def dwcohort2():
	saturate = [
		{"Cage_TreatmentProtocol_code":["cFluDW","Cage_Treatment_start_date","Cage_Treatment_end_date"]},
		{"TreatmentProtocol_code":["aFluIV","Treatment_start_date"]},
		{"TreatmentProtocol_code":["aFluSC","Treatment_start_date"]}
		]

	col_entries=[("Animal","id"),("Treatment",),("FMRIMeasurement",),("TreatmentProtocol","code"),("Cage","id"),("Cage","Treatment",""),("Cage","TreatmentProtocol","code")]
	join_entries=[("Animal.treatments",),("FMRIMeasurement",),("Treatment.protocol",),("Animal.cage_stays",),("CageStay.cage",),("Cage_Treatment","Cage.treatments"),("Cage_TreatmentProtocol","Cage_Treatment.protocol")]
	filters = [["Cage_Treatment","start_date","2016,5,19,23,5"]]

	# setting outerjoin to true will indirectly include controls
	reference_df = get_df("~/syncdata/meta.db",col_entries=col_entries, join_entries=join_entries, filters=filters, outerjoin=True)

	timetable.multi_plot(reference_df, "Animal_id", shade=["FMRIMeasurement_date"], saturate=saturate)
	plt.show()

def ipcohort():
	saturate = [
		{"Animal_TreatmentProtocol_code":["cFluIP","Animal_Treatment_start_date","Animal_Treatment_end_date"]},
		{"Animal_TreatmentProtocol_code":["aFluIV","Animal_Treatment_start_date"]},
		]

	col_entries=[("Animal","id"),("FMRIMeasurement",),("Animal","Treatment",""),("Animal","TreatmentProtocol","code")]
	join_entries=[("Animal.treatments",),("FMRIMeasurement",),("Animal_Treatment","Animal.treatments"),("Animal_TreatmentProtocol","Animal_Treatment.protocol")]
	filters = [["Treatment","start_date","2015,11,11"]]

	# setting outerjoin to true will indirectly include controls
	reference_df = get_df("~/syncdata/meta.db",col_entries=col_entries, join_entries=join_entries, filters=filters, outerjoin=True)

	timetable.multi_plot(reference_df, "Animal_id", shade=["FMRIMeasurement_date"], saturate=saturate, real_dates=False)
	plt.show()

if __name__ == '__main__':
	dwcohort1()
	# dwcohort2()
	# ipcohort()
