import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm
from matplotlib.ticker import MultipleLocator, LinearLocator
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import matplotlib.ticker as ticker

def draw_timeplan(rule, labels=None, blank_color=0.9):
	duration = np.shape(rule)[1]
	time_labels = [label +1 for label in range(duration)]

	cMap = add_grey(cm.viridis, blank_color)

	fig, ax = plt.subplots(figsize=np.shape(rule)[::-1] , facecolor='#eeeeee', tight_layout=True)
	im = ax.pcolorfast(rule, cmap=cMap)

	#place and null major ticks (we still need them for the grid)
	ax.xaxis.set_major_locator(LinearLocator(duration+1))
	ax.xaxis.set_major_formatter(ticker.NullFormatter())

	#place and format minor ticks (used to substitute for centered major tick labels)
	ax.xaxis.set_minor_locator(ticker.IndexLocator(1,0.5))
	ax.xaxis.set_minor_formatter(ticker.FixedFormatter(time_labels))

	#remove all major tick lines
	plt.setp(ax.get_xticklines(),visible=False)

	#remove bottom and top small tick lines
	for tick in ax.xaxis.get_minor_ticks():
		tick.tick1line.set_markersize(0)
		tick.tick2line.set_markersize(0)

	#Set only 7th minor tick label to visible
	ax.set_yticklabels(labels)
	for label in ax.xaxis.get_minorticklabels():
		label.set_visible(False)
	for label in ax.xaxis.get_minorticklabels()[::7]:
		label.set_visible(True)

	#Set yticks to labels and add 0.5 cell height offset
	ax.yaxis.set(ticks=np.arange(0.5, len(labels)))
	#Set yticks to point outside the figure
	ax.get_yaxis().set_tick_params(direction='out')
	#Rotate ytick labels
	plt.setp(ax.yaxis.get_majorticklabels(), rotation=30)
	#Constrain yticks to left side of figure
	ax.yaxis.set_ticks_position('left')

	# create grid
	ax.xaxis.grid(True, which='major', color='1', linestyle='-')

	#delete all spines
	for spine in ["right", "left", "top", "bottom"]:
		ax.spines[spine].set_visible(False)

	# recolour yticks in blank image color
	[t.set_color(str(blank_color)) for t in ax.yaxis.get_ticklines()]


	plt.show()
	# fig.set_size_inches(4.3,1)
	# fig.savefig("lala.pdf")

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

if __name__ == '__main__':
	labels = ["fMRI","iv Flu.","ip Flu."]
	rule = np.zeros((3,57))
	rule[0,::-14]=1
	rule[0,7]=1
	rule[0,0:2]=1
	rule[1,14]=2
	rule[2,15:42]=3
	draw_timeplan(rule, labels)
