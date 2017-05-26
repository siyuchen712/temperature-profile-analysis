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

from core.re_and_globals import *


def single_channel_analysis(df, channel, ambient, upper_threshold, lower_threshold):
	df_summary = pd.DataFrame()

	####Test for one channel
	df_chan = df[['Sweep #', 'Time']+[channel]]
	df_chan = df_chan.sort_values(['Sweep #'])
	df_chan = df_chan.reset_index(drop=True)
	sweep_screen = []
	for i in range(df_chan.shape[0]):
	    sweep_screen.append(i)
	df_chan.insert(0,'Sweep_screen',pd.Series(sweep_screen, index=df_chan.index).tolist())

	ls_cycle_bound = [] ## bounds rand to search each cycle for key points
	High_index = []  ## all poitns above high threshold
	Low_index = []  ## all points below low threshold
	ls_cycle = [] ## list of lists --> nested list is search bounds of sweep screen
	cycle_ls = []  ## list of integers - cycles that DID reach threhold(s)
	point_cycle_index = [] ## merged low and high key points for each cycle
	key_point_cycle = []  ## list holding dataframes of key cycle points
	n_reach = []  ## list of the "not-reach" cycles' keypoint dataframes
	n_reach_cycle = []  ## list of integers - cycles that DID NOT reach threhold(s)
	test = []  ## for debugging

	## i --> number of cycles based on ambient dataframe
	for i in range(ambient.shape[0]//4): 
	    cycle_ls.append(i)
	    ## find boundary to search
	    if i != ambient.shape[0]//4 - 1:  ## last loop
	    	ls_cycle_bound.append(ambient.iloc[[4*i,4*i+6]].Sweep_screen.tolist())
	    else:  ## not last loop 
	    	ls_cycle_bound.append(ambient.iloc[[4*i,ambient.shape[0]-1]].Sweep_screen.tolist())

	    if ls_cycle_bound[i][0] < 5: ## at beginning of profile (sweep screen smaller than 5)
	    	ls_cycle_bound[i][0] = 0
	    else: ## not at beginning
	    	ls_cycle_bound[i][0] = ls_cycle_bound[i][0] - 5

	    if ls_cycle_bound[i][1] > ambient.Sweep_screen[ambient.shape[0]-1] - 5: ## at end
	    	ls_cycle_bound[i][1] = ambient.Sweep_screen[ambient.shape[0]-1]
	    else:  ## not at end
	    	ls_cycle_bound[i][1] = ls_cycle_bound[i][1] + 5

	    ls_cycle_component = df_chan.iloc[ls_cycle_bound[i][0]:ls_cycle_bound[i][1]]
	    ls_cycle_component.insert(0,'cycle#',i+1)
	    ls_cycle.append(ls_cycle_component)
	    
	    #The index of all the points of temp out of threshold
	    High_index = ls_cycle[i][channel][ls_cycle[i][channel]> upper_threshold].index.tolist()
	    Low_index = ls_cycle[i][channel][ls_cycle[i][channel]< lower_threshold].index.tolist()
	    point_index = []
	    for m in range(int(len(Low_index))):
	        point_index.append(Low_index[m])
	    for n in range(int(len(High_index))):
	        point_index.append(High_index[n])   

	    point_index = np.sort(point_index)
	    point_index = point_index.tolist()
	    point_cycle_index.append(point_index)
	    ls_cycle[i] = ls_cycle[i].loc[point_cycle_index[i]]
	    

	    ## Gap point
	    result = ls_cycle[i]
	    result['diff_1_sweep#'] = ls_cycle[i][[1]].shift(-1) - ls_cycle[i][[1]]
	    result['diff_2_sweep#'] = ls_cycle[i][[1]] - ls_cycle[i][[1]].shift(1)
	    result = result.sort_values(['Sweep_screen'])
	    result = result.reset_index(drop=True)

	    ## Get the threshold of gap length
	    result_index_1 = result['diff_1_sweep#'][result['diff_1_sweep#'] >1].index.tolist()
	    result_index_2 = result['diff_2_sweep#'][result['diff_2_sweep#'] >1].index.tolist()
	    result_index = list(set(result_index_1) | set(result_index_2))
	    result = result.loc[result_index]
	    result = result.sort_values(['Sweep_screen'])
	    result = result.reset_index(drop=True)
   
	    test.append(result)
	    
	    if result.shape[0]< 5 and i!=ambient.shape[0]//4-1:
	        n_reach.append(result)
	        n_reach_cycle.append(i)
	    elif result.shape[0]< 4 and i ==ambient.shape[0]//4-1:
	        n_reach.append(result)
	        n_reach_cycle.append(i)
	    else:
	        result_points = result[[0,1,2,3,4]]
	        result_points = result_points.iloc[0:4]
	        key_point_cycle.append(result_points)

	for cycle in n_reach_cycle:  ## 
	    cycle_ls.remove(cycle)

	#### Cycle Statistics #####
	if len(key_point_cycle) == ambient.shape[0]//4:  ## if all the cycles reached
	    key = pd.concat(key_point_cycle)
	    #key = key.loc[cycle_index]
	    key = key.sort_values(['Sweep_screen'])
	    key = key.reset_index(drop=True)
	    
	    selected_channel = key
	    time_selected_channel = []
	    for m in range(selected_channel.shape[0]-1):
	        a1 = selected_channel['Time'][m+1]
	        a2 = selected_channel['Time'][m] 
	        time_selected_channel.append((datetime.strptime(a1, DATE_FORMAT) - datetime.strptime(a2, DATE_FORMAT)).total_seconds())
	    
	    time_selected_channel.append(0)
	    selected_channel.insert(0,'duration',time_selected_channel)

	    #Duration
	    selected_channel['duration_minutes'] = selected_channel['duration']/60
	    #temp_range
	    selected_channel['ramp_temp'] = pd.Series(0, index=result.index)
	    selected_channel['ramp_temp'] = selected_channel[[5]].shift(-1) - selected_channel[[5]]
	    #RAMP
	    selected_channel['ramp_rate'] = pd.Series(0, index=result.index)
	    selected_channel['ramp_rate'] = selected_channel['ramp_temp']*60/selected_channel['duration']
	    
	    df_direction = selected_channel
	    ls_index_1 = []
	    ls_index_2 = []
	    ls_index_3 = []
	    ls_index_4 = []
	    for i in range(int(selected_channel.shape[0]/4)):
	        ls_index_1.append(i*4)
	        ls_index_2.append(i*4 + 2)
	        ls_index_3.append(i*4 + 1)
	        ls_index_4.append(i*4 + 3)
	    df_direction1 = selected_channel.loc[ls_index_1]
	    df_direction1 = df_direction1.sort_values(['Sweep_screen'])
	    df_transform1 = df_direction1.reset_index(drop=True)
	    df_direction2 = selected_channel.loc[ls_index_2]
	    df_direction2 = df_direction2.sort_values(['Sweep_screen'])
	    df_transform2 = df_direction2.reset_index(drop=True)

	    df_soak1 = selected_channel.loc[ls_index_3]
	    df_soak1 = df_soak1.sort_values(['Sweep_screen'])
	    df_soak1 = df_soak1.reset_index(drop=True)
	    df_soak2 = selected_channel.loc[ls_index_4]
	    df_soak2 = df_soak2.sort_values(['Sweep_screen'])
	    df_soak2 = df_soak2.reset_index(drop=True)
	    mean_temp_1 = []
	    mean_temp_2 = []
	    max_temp_1 = []
	    max_temp_2 = []
	    min_temp_1 = []
	    min_temp_2 = []
	    for i in range(int(selected_channel.shape[0]/4)-1):
	        mean_temp_1.append(df_chan.iloc[selected_channel.iloc[4*i+1]['Sweep_screen']:selected_channel.iloc[4*i+2]['Sweep_screen'],[3]].mean(axis=0) .ix[0])
	        mean_temp_2.append(df_chan.iloc[selected_channel.iloc[4*i+3]['Sweep_screen']:selected_channel.iloc[4*i+4]['Sweep_screen'],[3]].mean(axis=0) .ix[0])
	        max_temp_1.append(df_chan.iloc[selected_channel.iloc[4*i+1]['Sweep_screen']:selected_channel.iloc[4*i+2]['Sweep_screen'],[3]].max(axis=0) .ix[0])
	        max_temp_2.append(df_chan.iloc[selected_channel.iloc[4*i+3]['Sweep_screen']:selected_channel.iloc[4*i+4]['Sweep_screen'],[3]].max(axis=0) .ix[0])
	        min_temp_1.append(df_chan.iloc[selected_channel.iloc[4*i+1]['Sweep_screen']:selected_channel.iloc[4*i+2]['Sweep_screen'],[3]].min(axis=0) .ix[0])
	        min_temp_2.append(df_chan.iloc[selected_channel.iloc[4*i+3]['Sweep_screen']:selected_channel.iloc[4*i+4]['Sweep_screen'],[3]].min(axis=0) .ix[0])     

	    df_soak1['mean_temp'] = pd.Series(mean_temp_1)
	    df_soak2['mean_temp'] = pd.Series(mean_temp_2)
	    df_soak1['max_temp'] = pd.Series(max_temp_1)
	    df_soak2['max_temp'] = pd.Series(max_temp_2)
	    df_soak1['min_temp'] = pd.Series(min_temp_1)
	    df_soak2['min_temp'] = pd.Series(min_temp_2)
	    result_each_cycle = pd.concat([df_soak1[[1,6,9,10,11]], df_soak2[[6,9,10,11]],df_transform1[[6,7,8]] ,df_transform2[[6,7,8]]], axis=1)
	    
	    if (result_each_cycle.ix[:,2].mean())> 90:
	        summary_lable = ['cycle#', 'hot_soak_duration_minute', 'hot_soak_mean_temp_c', 'hot_soak_max_temp_c', 'hot_soak_min_temp_c', 'cold_soak_duration_minute', 'cold_soak_mean_temp_c', 'cold_soak_max_temp_c', 'cold_soak_min_temp_c', 'up_recovery_time_minute', 'up_RAMP_temp_c', 'up_RAMP_rate_c/minute', 'down_recovery_time_minute', 'down_RAMP_temp_c', 'down_RAMP_rate_c/minute']
	    else:
	        summary_lable = ['cycle#', 'cold_soak_duration_minute', 'cold_soak_mean_temp_c', 'cold_soak_max_temp_c', 'cold_soak_min_temp_c', 'hot_soak_duration_minute', 'hot_soak_mean_temp_c', 'hot_soak_max_temp_c', 'hot_soak_min_temp_c', 'down_recovery_time_minute', 'down_RAMP_temp_c', 'down_RAMP_rate_c/minute', 'up_recovery_time_minute', 'up_RAMP_temp_c', 'up_RAMP_rate_c/minute']

	    result_each_cycle.columns = summary_lable

	    ls_mean = []
	    ls_std = []
	    ls_min = []
	    ls_min_cid = []
	    ls_max = []
	    ls_max_cid = []
	    for i in range(1,result_each_cycle.shape[1]):
	        ls_mean.append(result_each_cycle.ix[:,i].mean())
	        ls_std.append(result_each_cycle.ix[:,i].std())
	        ls_max.append(result_each_cycle.ix[:,i].max())
	        ls_min.append(result_each_cycle.ix[:,i].min())
	        ls_min_cid.append(result_each_cycle.ix[:,i].idxmin())
	        ls_max_cid.append(result_each_cycle.ix[:,i].idxmax())
	    df_summary = pd.DataFrame.from_items([('mean', ls_mean), ('min', ls_min),('min_cycle#', ls_min_cid), ('max', ls_max), ('max_cycle#', ls_max_cid),('std_dev', ls_std)],orient='index', columns=summary_lable[1:])

	    df_summary = df_summary.round(2)
	    result_each_cycle = result_each_cycle.round(2)


	else:  ## not all cycles reached thresholds
	    consequtive_cycle = []
	    for k, g in itertools.groupby(enumerate(cycle_ls), lambda x: x[1]-x[0] ) :
	        consequtive_cycle.append(list(map(itemgetter(1), g)))
	    
	    uncontn_cycle = []
	    for k in range(len(consequtive_cycle)):
	        uncontn_cycle.append([])
	        for i in consequtive_cycle[k]:
	            for j in range(len(key_point_cycle)):
	                if key_point_cycle[j]['cycle#'][0] == i+1:
	                    uncontn_cycle[k].append(key_point_cycle[j])
	                    
	    uncontn_result_each_cycle = []
	    uncontn_summary = []

	    for x in range(len(uncontn_cycle)):
	        uncontn_result_each_cycle.append([])
	        uncontn_summary.append([])

	        key = pd.concat(uncontn_cycle[x])
	        #key = key.loc[cycle_index]
	        key = key.sort_values(['Sweep_screen'])
	        key = key.reset_index(drop=True)

	        selected_channel = key
	        time_selected_channel = []
	        for m in range(selected_channel.shape[0]-1):
	            a1 = selected_channel['Time'][m+1]
	            a2 = selected_channel['Time'][m] 
	            time_selected_channel.append((datetime.strptime(a1,DATE_FORMAT) - datetime.strptime(a2,DATE_FORMAT)).total_seconds())

	        time_selected_channel.append(0)
	        selected_channel.insert(0,'duration',time_selected_channel)

	        #Duration
	        selected_channel['duration_minutes'] = selected_channel['duration']/60
	        #temp_range
	        selected_channel['ramp_temp'] = pd.Series(0, index=result.index)
	        selected_channel['ramp_temp'] = selected_channel[[2]].shift(-1) - selected_channel[[2]]
	        #RAMP
	        selected_channel['ramp_rate'] = pd.Series(0, index=result.index)
	        selected_channel['ramp_rate'] = selected_channel['ramp_temp']*60/selected_channel['duration']

	        df_direction = selected_channel
	        ls_index_1 = []
	        ls_index_2 = []
	        ls_index_3 = []
	        ls_index_4 = []
	        for i in range(int(selected_channel.shape[0]/4)):
	            ls_index_1.append(i*4)
	            ls_index_2.append(i*4 + 2)
	            ls_index_3.append(i*4 + 1)
	            ls_index_4.append(i*4 + 3)
	        df_direction1 = selected_channel.loc[ls_index_1]
	        df_direction1 = df_direction1.sort_values(['Sweep_screen'])
	        df_transform1 = df_direction1.reset_index(drop=True)
	        df_direction2 = selected_channel.loc[ls_index_2]
	        df_direction2 = df_direction2.sort_values(['Sweep_screen'])
	        df_transform2 = df_direction2.reset_index(drop=True)

	        df_soak1 = selected_channel.loc[ls_index_3]
	        df_soak1 = df_soak1.sort_values(['Sweep_screen'])
	        df_soak1 = df_soak1.reset_index(drop=True)
	        df_soak2 = selected_channel.loc[ls_index_4]
	        df_soak2 = df_soak2.sort_values(['Sweep_screen'])
	        df_soak2 = df_soak2.reset_index(drop=True)
	        mean_temp_1 = []
	        mean_temp_2 = []
	        max_temp_1 = []
	        max_temp_2 = []
	        min_temp_1 = []
	        min_temp_2 = []
	        for i in range(int(selected_channel.shape[0]/4)-1):
	            mean_temp_1.append(df_chan.iloc[selected_channel.iloc[4*i+1]['Sweep_screen']:selected_channel.iloc[4*i+2]['Sweep_screen'],[3]].mean(axis=0) .ix[0])
	            mean_temp_2.append(df_chan.iloc[selected_channel.iloc[4*i+3]['Sweep_screen']:selected_channel.iloc[4*i+4]['Sweep_screen'],[3]].mean(axis=0) .ix[0])
	            max_temp_1.append(df_chan.iloc[selected_channel.iloc[4*i+1]['Sweep_screen']:selected_channel.iloc[4*i+2]['Sweep_screen'],[3]].max(axis=0) .ix[0])
	            max_temp_2.append(df_chan.iloc[selected_channel.iloc[4*i+3]['Sweep_screen']:selected_channel.iloc[4*i+4]['Sweep_screen'],[3]].max(axis=0) .ix[0])
	            min_temp_1.append(df_chan.iloc[selected_channel.iloc[4*i+1]['Sweep_screen']:selected_channel.iloc[4*i+2]['Sweep_screen'],[3]].min(axis=0) .ix[0])
	            min_temp_2.append(df_chan.iloc[selected_channel.iloc[4*i+3]['Sweep_screen']:selected_channel.iloc[4*i+4]['Sweep_screen'],[3]].min(axis=0) .ix[0])     

	        df_soak1['mean_temp'] = pd.Series(mean_temp_1)
	        df_soak2['mean_temp'] = pd.Series(mean_temp_2)
	        df_soak1['max_temp'] = pd.Series(max_temp_1)
	        df_soak2['max_temp'] = pd.Series(max_temp_2)
	        df_soak1['min_temp'] = pd.Series(min_temp_1)
	        df_soak2['min_temp'] = pd.Series(min_temp_2)
	        result_each_cycle = pd.concat([df_soak1[[1,6,9,10,11]], df_soak2[[6,9,10,11]],df_transform1[[6,7,8]] ,df_transform2[[6,7,8]]], axis=1)

	        if (result_each_cycle.ix[:,2].mean())> 90:
	            summary_lable = ['cycle#', 'hot_soak_duration_minute', 'hot_soak_mean_temp_c', 'hot_soak_max_temp_c', 'hot_soak_min_temp_c', 'cold_soak_duration_minute', 'cold_soak_mean_temp_c', 'cold_soak_max_temp_c', 'cold_soak_min_temp_c', 'up_recovery_time_minute', 'up_RAMP_temp_c', 'up_RAMP_rate_c/minute', 'down_recovery_time_minute', 'down_RAMP_temp_c', 'down_RAMP_rate_c/minute']
	        else:
	            summary_lable = ['cycle#', 'cold_soak_duration_minute', 'cold_soak_mean_temp_c', 'cold_soak_max_temp_c', 'cold_soak_min_temp_c', 'hot_soak_duration_minute', 'hot_soak_mean_temp_c', 'hot_soak_max_temp_c', 'hot_soak_min_temp_c', 'down_recovery_time_minute', 'down_RAMP_temp_c', 'down_RAMP_rate_c/minute', 'up_recovery_time_minute', 'up_RAMP_temp_c', 'up_RAMP_rate_c/minute']

	        result_each_cycle.columns = summary_lable

	        ls_mean = []
	        ls_std = []
	        ls_min = []
	        ls_min_cid = []
	        ls_max = []
	        ls_max_cid = []
	        for i in range(1,result_each_cycle.shape[1]):
	            ls_mean.append(result_each_cycle.ix[:,i].mean())
	            ls_std.append(result_each_cycle.ix[:,i].std())
	            ls_max.append(result_each_cycle.ix[:,i].max())
	            ls_min.append(result_each_cycle.ix[:,i].min())
	            ls_min_cid.append(result_each_cycle.ix[:,i].idxmin())
	            ls_max_cid.append(result_each_cycle.ix[:,i].idxmax())
	        df_summary = pd.DataFrame.from_items([('mean', ls_mean), ('min', ls_min),('min_cycle#', ls_min_cid), ('max', ls_max), ('max_cycle#', ls_max_cid),('std_dev', ls_std)],orient='index', columns=summary_lable[1:])

	        df_summary = df_summary.round(2)
	        result_each_cycle = result_each_cycle.round(2)

	        uncontn_result_each_cycle[x] = result_each_cycle
	        uncontn_summary[x] = df_summary
	
	return result_each_cycle, df_summary
