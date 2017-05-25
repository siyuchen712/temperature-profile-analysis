import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time
import re
from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.plotly as py
import plotly.graph_objs as go
from operator import itemgetter
import itertools
import xlsxwriter

from ambient import *
from not_ambient import *

def analyze_all_channels(df, channels, amb):
	writer = create_wb()
	
	## analyze ambient
	result_each_cycle, df_summary_amb, ambient = ambient_analysis(df, channels, amb, UPPER_THRESHOLD, LOWER_THRESHOLD)
	df_summary_amb.to_excel(writer, 'Amb '+str(amb))

	### all other channels
	for channel in channels:
		print(channel)
		if channel != amb:
			df_summary_tc = pd.DataFrame()
			df_summary_tc = single_channel_analysis(df, channel, ambient)
			df_summary_tc.to_excel(writer, channel)
	writer.save()

def create_wb():
    writer = pd.ExcelWriter('output.xlsx')
    return writer
