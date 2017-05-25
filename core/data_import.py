import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time
import re
##from plotly import __version__
##from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.plotly as py
import plotly.graph_objs as go
from operator import itemgetter
import itertools

# from core.plot import *
# from core.analysis import *

from plot import *
from analysis import *
from re_and_globals import *

## init_notebook_mode(connected=True)  ## ???

py.sign_in('sjbrun','v1jdPUhNoRgRBpAOOx7Y')


######  READING IN DATA AND SETTING UP PARAMETERS
def read_data_for_plot(datapath):
	''' Returns a dataframe of the agilent temperature data '''
	date_parser = lambda x: pd.datetime.strptime(x, '%m/%d/%Y %H:%M:%S:%f')
	return pd.read_csv(datapath, parse_dates={'Date Time': [1]}, date_parser=date_parser, 
					   index_col='Date Time', engine='python')

def read_data_for_analysis(datapath):
	''' Returns a dataframe of the agilent temperature data '''
	date_parser = lambda x: pd.datetime.strptime(x, '%m/%d/%Y %H:%M:%S:%f')
	return pd.read_csv(datapath)	

def get_channels(df):
	''' Find valid TC channel headers in dataframe '''
	return [df.columns[i] for i in range(len(df.columns)) if re.search(REGEX_TEMP_COL, df.columns[i])]

def set_ambient(channels, ambient_channel_number):
	''' Sets the ambient TC from user input integer '''
	return channels[ambient_channel_number-1]

def drop_errors(df, channels):
	''' Get rid of outrage data and output error list '''
	df_copy = df
	for channel in channels:
	    df = df[df[channel] < 150]
	    df = df[df[channel] > -100]
	errors = df_copy[~df_copy['Sweep #'].isin(df['Sweep #'].tolist())]
	return df, errors

def import_data(datapath, ambient_channel_number):
	df = read_data_for_plot(datapath)
	channels = get_channels(df)
	amb = set_ambient(channels, ambient_channel_number)
	df, errors = drop_errors(df, channels)
	return df, channels, amb, errors


## DATA IMPORT
df, channels, amb, errors = import_data(DATAPATH, ambient_channel_number)

## PLOT
#plot_profile(TITLE, df, channels)

## ANALYSIS
df = read_data_for_analysis(DATAPATH)
analyze_all_channels(df, channels, amb)


## ambient
# result_each_cycle, df_summary, ambient = ambient_analysis(df, channels, amb, UPPER_THRESHOLD, LOWER_THRESHOLD)

# ## not_ambient
# channel = channels[3]
# df_summary2 = single_channel_analysis(df, channel, ambient)