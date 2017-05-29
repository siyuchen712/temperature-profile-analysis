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


def analyze_all_channels(df, channels, amb, amb_errors, tc_channel_names, upper_threshold, lower_threshold, tolerance, rate_adjustment):
    writer = create_wb() ## create workbook
    
    ## analyze ambient
    amb_upper_threshold = upper_threshold - tolerance
    amb_lower_threshold = lower_threshold + tolerance
    result_each_cycle_amb, df_summary_amb, ambient = ambient_analysis(df, channels, amb, amb_upper_threshold, amb_lower_threshold)
    write_multiple_dfs(writer, [amb_errors, df_summary_amb, result_each_cycle_amb], 'Amb '+str(amb), 3)

    ### all other channels
    if rate_adjustment:  ## apply rate adjustment if supplied
        temp_adjustment = rate_adjustment*(float(upper_threshold) - float(lower_threshold))
        upper_threshold = upper_threshold - temp_adjustment
        lower_threshold = lower_threshold + temp_adjustment
    else: ## otherwise use tolerance used for ambient
        upper_threshold = amb_upper_threshold
        lower_threshold = amb_lower_threshold
        
    for channel in channels:
        print(channel)
        if channel != amb:
            result_each_cycle, df_summary_tc, n_reach_summary = pd.DataFrame(), pd.DataFrame(), pd.DataFrame() ## ensure reset
            result_each_cycle, df_summary_tc, n_reach_summary= single_channel_analysis(df, channel, ambient, upper_threshold, lower_threshold)
            if tc_channel_names[channel]:
                tc_name = tc_channel_names[channel] + ' (' + channel.split(' ')[1] + ')'
            else:
                tc_name = channel
            write_multiple_dfs(writer, [df_summary_tc, result_each_cycle, n_reach_summary], tc_name, 3)
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
