import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.colors import LinearSegmentedColormap

def add_grey(cMap, blank_color):
	cdict = {
		'red': [],
		'green': [],
		'blue': [],
		'alpha': []
	}

	# regular index to compute the colors
	reg_index = np.linspace(0, 1, 254)

	# shifted index to match the data
	shift_index = np.linspace(0, 1, 256)

	grey_count=0
	grey_shades=2
	for ix, si in enumerate(shift_index):
		grey_count +=1
		if grey_count <= grey_shades:
			cdict['red'].append((si, blank_color, blank_color))
			cdict['green'].append((si, blank_color, blank_color))
			cdict['blue'].append((si, blank_color, blank_color))
			cdict['alpha'].append((si, 1, 1))
		else:
			ri = reg_index[ix-grey_shades]
			r, g, b, a = cMap(ri)
			cdict['red'].append((si, r, r))
			cdict['green'].append((si, g, g))
			cdict['blue'].append((si, b, b))
			cdict['alpha'].append((si, a, a))

	return LinearSegmentedColormap("name", cdict)

def ttp_style(ax, df_):
	#place and null major ticks (we still need them for the grid)
	ax.xaxis.set_major_locator(ticker.LinearLocator(len(df_.index)+1))
	ax.xaxis.set_major_formatter(ticker.NullFormatter())
	ax.yaxis.set_major_locator(ticker.LinearLocator(len(df_.columns)+1))
	ax.yaxis.set_major_formatter(ticker.NullFormatter())

	#place and format minor ticks (used to substitute for centered major tick labels)
	ax.xaxis.set_minor_locator(ticker.IndexLocator(1,0.5))
	ax.xaxis.set_minor_formatter(ticker.FixedFormatter(df_.index))
	ax.yaxis.set_minor_locator(ticker.IndexLocator(1,0.5))
	ax.yaxis.set_minor_formatter(ticker.FixedFormatter(df_.columns))

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

	return ax
