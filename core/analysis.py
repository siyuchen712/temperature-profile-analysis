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


def analyze_all_channels(df, channels, amb, amb_errors, tc_channel_names, upper_threshold, lower_threshold, rate_adjustment):
	writer = create_wb() ## create workbook
	
	## analyze ambient
	result_each_cycle_amb, df_summary_amb, ambient = ambient_analysis(df, channels, amb, upper_threshold, lower_threshold)
	write_multiple_dfs(writer, [amb_errors, df_summary_amb, result_each_cycle_amb], 'Amb '+str(amb), 3)

	### all other channels
	if rate_adjustment:
		temp_adjustment = float(rate_adjustment)*(int(upper_threshold) - int(lower_threshold))
		upper_threshold = upper_threshold - temp_adjustment
		lower_threshold = lower_threshold + temp_adjustment
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

def write_multiple_dfs(writer, df_list, worksheet_name, spaces):
    row = 0
    for dataframe in df_list:
        dataframe.to_excel(writer, sheet_name=worksheet_name, startrow=row , startcol=0)   
        row = row + len(dataframe.index) + spaces + 1
    # don't save (wait for other thermocouples)