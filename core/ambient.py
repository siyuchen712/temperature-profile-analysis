import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time
import re
from operator import itemgetter
import itertools

from core.re_and_globals import *


def ambient_analysis(df, channels, amb, upper_threshold, lower_threshold):
    #########get the big gap of ambient (channel_1)
    ####Test for one channel
    df_chan_Ambient = df[['Sweep #', 'Time', amb]]
    #df_chan_Ambient = df_chan_Ambient.sort_values(['Sweep #'])
    df_chan_Ambient = df_chan_Ambient.reset_index(drop=True)
    sweep_screen = []
    for i in range(df_chan_Ambient.shape[0]):
        sweep_screen.append(i)
    df_chan_Ambient.insert(0,'Sweep_screen',pd.Series(sweep_screen, index=df_chan_Ambient.index).tolist())

    #The index of all the points of temp out of threshold
    High_index = df_chan_Ambient[channels[0]][df_chan_Ambient[channels[0]]> upper_threshold].index.tolist()
    Low_index = df_chan_Ambient[channels[0]][df_chan_Ambient[channels[0]]< lower_threshold].index.tolist()
    point_index = []
    for i in range(len(Low_index)):
        point_index.append(Low_index[i])
    for i in range(len(High_index)):
        point_index.append(High_index[i])   

    point_index = np.sort(point_index)
    point_index = point_index.tolist()
        
    df_chan_Ambient_loc = df_chan_Ambient.loc[point_index]

    ####Gap point
    result = df_chan_Ambient_loc
    result['diff_1_sweep#'] = df_chan_Ambient_loc[[0]].shift(-1) - df_chan_Ambient_loc[[0]]
    result['diff_2_sweep#'] = df_chan_Ambient_loc[[0]] - df_chan_Ambient_loc[[0]].shift(1)
    result = result.sort_values(['Sweep_screen'])
    result = result.reset_index(drop=True)

    #Get the threshold of gap length
    result_index_1 = result['diff_1_sweep#'][result['diff_1_sweep#'] >1].index.tolist()
    result_index_2 = result['diff_2_sweep#'][result['diff_2_sweep#'] >1].index.tolist()
    result_index = list(set(result_index_1) | set(result_index_2))
    result = result.loc[result_index]
    result = result.sort_values(['Sweep_screen'])
    result = result.reset_index(drop=True)

    result_points_1 = result[[0,1,2,3]]
    result_points_1.insert(0,'diff_1_sweep#',(result_points_1[[0]].shift(-1) - result_points_1[[0]]).Sweep_screen.values.tolist())
    result_points_1.insert(0,'diff_2_sweep#',(result_points_1[[1]] - result_points_1[[1]].shift(1)).Sweep_screen.values.tolist())

    ripple_gap = (result_points_1['diff_1_sweep#'] + result_points_1['diff_2_sweep#']).mean()*0.5  ## TO DO --> set valid ratio
    cycle_index = result_points_1['diff_1_sweep#'][result_points_1['diff_1_sweep#'] + result_points_1['diff_2_sweep#']>ripple_gap].index.tolist()
    cycle_index.append(0)
    
    result_points_1 = result_points_1.loc[cycle_index]
    result_points_1 = result_points_1.sort_values(['Sweep_screen'])
    result_points_1 = result_points_1.reset_index(drop=True)
    result_points_1 = result_points_1[[2,3,4,5]]

    ambient = result_points_1

    ### Adds time duration
    time = []
    for m in range(ambient.shape[0]-1):
        a1 = ambient['Time'][m+1]
        a2 = ambient['Time'][m]
        time.append((datetime.strptime(a1, DATE_FORMAT) - datetime.strptime(a2, DATE_FORMAT)).total_seconds())

    time.append(0)
    ambient.insert(0,'duration',time)
    ambient['duration_minutes'] = ambient['duration']/60 ## translate duration to minutes


    # temp range difference of consecutive rows
    ambient['ramp_temp'] = pd.Series(0, index=result.index)
    ambient['ramp_temp'] = ambient[[4]].shift(-1) - ambient[[4]]
    
    # Find ramp rates
    ambient['ramp_rate'] = pd.Series(0, index=result.index)
    ambient['ramp_rate'] = ambient['ramp_temp']*60/ambient['duration']


    ### differentiate profile starting point --> high to low or low to high
    
    if ambient['ramp_temp'][0]>100:  ## high to low
        df_direction = ambient
        ls_index_1 = []
        ls_index_2 = []
        ls_index_3 = []
        ls_index_4 = []
        for i in range(int(ambient.shape[0]/4)):
            ls_index_1.append(i*4)
            ls_index_2.append(i*4 + 2)
            ls_index_3.append(i*4 + 1)
            ls_index_4.append(i*4 + 3)
        df_direction1 = ambient.loc[ls_index_1]
        df_direction1 = df_direction1.sort_values(['Sweep_screen'])
        df_transform1 = df_direction1.reset_index(drop=True)
        df_direction2 =ambient.loc[ls_index_2]
        df_direction2 = df_direction2.sort_values(['Sweep_screen'])
        df_transform2 = df_direction2.reset_index(drop=True)

        df_soak1 = ambient.loc[ls_index_3]
        df_soak1 = df_soak1.sort_values(['Sweep_screen'])
        df_soak1 = df_soak1.reset_index(drop=True)
        df_soak2 = ambient.loc[ls_index_4]
        df_soak2 = df_soak2.sort_values(['Sweep_screen'])
        df_soak2 = df_soak2.reset_index(drop=True)
        mean_temp_1 = []
        mean_temp_2 = []
        max_temp_1 = []
        max_temp_2 = []
        min_temp_1 = []
        min_temp_2 = []
        for i in range(int(ambient.shape[0]/4)):
            mean_temp_1.append(df_chan_Ambient.iloc[ambient.iloc[4*i+1]['Sweep_screen']:ambient.iloc[4*i+2]['Sweep_screen'],[3]].mean(axis=0) .ix[0])
            mean_temp_2.append(df_chan_Ambient.iloc[ambient.iloc[4*i+3]['Sweep_screen']:ambient.iloc[4*i+4]['Sweep_screen'],[3]].mean(axis=0) .ix[0])
            max_temp_1.append(df_chan_Ambient.iloc[ambient.iloc[4*i+1]['Sweep_screen']:ambient.iloc[4*i+2]['Sweep_screen'],[3]].max(axis=0) .ix[0])
            max_temp_2.append(df_chan_Ambient.iloc[ambient.iloc[4*i+3]['Sweep_screen']:ambient.iloc[4*i+4]['Sweep_screen'],[3]].max(axis=0) .ix[0])
            min_temp_1.append(df_chan_Ambient.iloc[ambient.iloc[4*i+1]['Sweep_screen']:ambient.iloc[4*i+2]['Sweep_screen'],[3]].min(axis=0) .ix[0])
            min_temp_2.append(df_chan_Ambient.iloc[ambient.iloc[4*i+3]['Sweep_screen']:ambient.iloc[4*i+4]['Sweep_screen'],[3]].min(axis=0) .ix[0])     

        df_soak1['mean_temp'] = pd.Series(mean_temp_1, index=df_soak1.index)
        df_soak2['mean_temp'] = pd.Series(mean_temp_2, index=df_soak2.index)
        df_soak1['max_temp'] = pd.Series(max_temp_1, index=df_soak1.index)
        df_soak2['max_temp'] = pd.Series(max_temp_2, index=df_soak2.index)
        df_soak1['min_temp'] = pd.Series(min_temp_1, index=df_soak1.index)
        df_soak2['min_temp'] = pd.Series(min_temp_2, index=df_soak2.index)
        
    else:  ## low to high
        df_direction = ambient
        ls_index_1 = []
        ls_index_2 = []
        ls_index_3 = []
        ls_index_4 = []
        for i in range(int(ambient.shape[0]/4)):
            ls_index_1.append(i*4 + 1)
            ls_index_2.append(i*4 + 3)
            ls_index_3.append(i*4)
            ls_index_4.append(i*4 + 2)
        df_direction1 = ambient.loc[ls_index_1]
        df_direction1 = df_direction1.sort_values(['Sweep_screen'])
        df_transform1 = df_direction1.reset_index(drop=True)
        df_direction2 =ambient.loc[ls_index_2]
        df_direction2 = df_direction2.sort_values(['Sweep_screen'])
        df_transform2 = df_direction2.reset_index(drop=True)

        df_soak1 = ambient.loc[ls_index_3]
        df_soak1 = df_soak1.sort_values(['Sweep_screen'])
        df_soak1 = df_soak1.reset_index(drop=True)
        df_soak2 = ambient.loc[ls_index_4]
        df_soak2 = df_soak2.sort_values(['Sweep_screen'])
        df_soak2 = df_soak2.reset_index(drop=True)
        mean_temp_1 = []
        mean_temp_2 = []
        max_temp_1 = []
        max_temp_2 = []
        min_temp_1 = []
        min_temp_2 = []
        for i in range(int(ambient.shape[0]/4)):
            mean_temp_1.append(df_chan_Ambient.iloc[ambient.iloc[4*i+1]['Sweep_screen']:ambient.iloc[4*i+2]['Sweep_screen'],[3]].mean(axis=0) .ix[0])
            mean_temp_2.append(df_chan_Ambient.iloc[ambient.iloc[4*i+3]['Sweep_screen']:ambient.iloc[4*i+4]['Sweep_screen'],[3]].mean(axis=0) .ix[0])
            max_temp_1.append(df_chan_Ambient.iloc[ambient.iloc[4*i+1]['Sweep_screen']:ambient.iloc[4*i+2]['Sweep_screen'],[3]].max(axis=0) .ix[0])
            max_temp_2.append(df_chan_Ambient.iloc[ambient.iloc[4*i+3]['Sweep_screen']:ambient.iloc[4*i+4]['Sweep_screen'],[3]].max(axis=0) .ix[0])
            min_temp_1.append(df_chan_Ambient.iloc[ambient.iloc[4*i+1]['Sweep_screen']:ambient.iloc[4*i+2]['Sweep_screen'],[3]].min(axis=0) .ix[0])
            min_temp_2.append(df_chan_Ambient.iloc[ambient.iloc[4*i+3]['Sweep_screen']:ambient.iloc[4*i+4]['Sweep_screen'],[3]].min(axis=0) .ix[0])     

        df_soak1['mean_temp'] = pd.Series(mean_temp_1, index=df_soak1.index)
        df_soak2['mean_temp'] = pd.Series(mean_temp_2, index=df_soak2.index)
        df_soak1['max_temp'] = pd.Series(max_temp_1, index=df_soak1.index)
        df_soak2['max_temp'] = pd.Series(max_temp_2, index=df_soak2.index)
        df_soak1['min_temp'] = pd.Series(min_temp_1, index=df_soak1.index)
        df_soak2['min_temp'] = pd.Series(min_temp_2, index=df_soak2.index)

    result_each_cycle = pd.concat([df_soak1[[5,8,9,10]], df_soak2[[5,8,9,10]],df_transform1[[5,6,7]] ,df_transform2[[5,6,7]]], axis=1)
    #result_each_cycle.columns = ['1_soak_duration_min', '1_soak_mean_temp', '1_soak_max_temp', '1_soak_min_temp', '2_soak_duration_min', '2_soak_mean_temp', '2_soak_max_temp', '2_soak_min_temp', '1_recovery_time', '1_RAMP_temp', '1_RAMP_rate', '2_recovery_time', '2_RAMP_temp', '2_RAMP_rate']

    result_each_cycle['cycle'] = pd.Series(list(range(1,result_each_cycle.shape[0]+1)), index=result_each_cycle.index)
    if (result_each_cycle.ix[:,1].mean())> 90:
        summary_lable = ['hot_soak_duration_minute', 'hot_soak_mean_temp_c', 'hot_soak_max_temp_c', 'hot_soak_min_temp_c', 'cold_soak_duration_minute', 'cold_soak_mean_temp_c', 'cold_soak_max_temp_c', 'cold_soak_min_temp_c', 'up_recovery_time_minute', 'up_RAMP_temp_c', 'up_RAMP_rate_c/minute', 'down_recovery_time_minute', 'down_RAMP_temp_c', 'down_RAMP_rate_c/minute', 'cycle#']
    else:
        summary_lable = ['-37_soak_duration_minute', '-37_soak_mean_temp_c', '-37_soak_max_temp_c', '-37_soak_min_temp_c', '92_soak_duration_minute', '92_soak_mean_temp_c', '92_soak_max_temp_c', '92_soak_min_temp_c', 'down_recovery_time_minute', 'down_RAMP_temp_c', 'down_RAMP_rate_c/minute', 'up_recovery_time_minute', 'up_RAMP_temp_c', 'up_RAMP_rate_c/minute', 'cycle#']
    result_each_cycle.columns = summary_lable

    ls_mean = []
    ls_std = []
    ls_min = []
    ls_min_cid = []
    ls_max = []
    ls_max_cid = []
    for i in range(result_each_cycle.shape[1]):
        ls_mean.append(result_each_cycle.ix[:,i].mean())
        ls_std.append(result_each_cycle.ix[:,i].std())
        ls_max.append(result_each_cycle.ix[:,i].max())
        ls_min.append(result_each_cycle.ix[:,i].min())
        ls_min_cid.append(result_each_cycle.ix[:,i].idxmin())
        ls_max_cid.append(result_each_cycle.ix[:,i].idxmax())
    df_summary = pd.DataFrame.from_items([('mean', ls_mean), ('min', ls_min),('min_cycle#', ls_min_cid), ('max', ls_max), ('max_cycle#', ls_max_cid),('std_dev', ls_std)],orient='index', columns=summary_lable)
    df_summary = df_summary.iloc[:, :14]

    result_each_cycle = result_each_cycle[[14,0,1,2,3,4,5,6,7,8,9,10,11,12,13]]

    df_summary = df_summary.round(2)
    result_each_cycle = result_each_cycle.round(2)

    return result_each_cycle, df_summary, ambient