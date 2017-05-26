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

from core.ambient import *
from core.not_ambient import *


def analyze_all_channels(df, channels, amb, tc_channel_names, upper_threshold, lower_threshold):
	writer = create_wb()
	
	## analyze ambient
	result_each_cycle_amb, df_summary_amb, ambient = ambient_analysis(df, channels, amb, upper_threshold, lower_threshold)
	result_each_cycle_amb.to_excel(writer, 'Amb '+str(amb))

	### all other channels
	for channel in channels:
		print(channel)
		if channel != amb:
			result_each_cycle, df_summary_tc = pd.DataFrame(), pd.DataFrame()
			result_each_cycle, df_summary_tc = single_channel_analysis(df, channel, ambient, upper_threshold, lower_threshold)
			if tc_channel_names[channel]:
				tc_name = tc_channel_names[channel] + ' (' + channel.split(' ')[1] + ')'
			else:
				tc_name = channel
			result_each_cycle.to_excel(writer, tc_name)
	writer.save()

def create_wb():
    writer = pd.ExcelWriter('output.xlsx')
    return writer
