from core.re_and_globals import *
from core.ambient import *
from core.data_import import *

# def retrieve_thermocouple_channels(datapath):
#     df_temp = pd.read_csv(datapath, nrows=5)
#     return [df.columns[i] for i in range(len(df.columns)) if re.search(REGEX_TEMP_COL, df.columns[i])]

datapath = r"C:\Users\bruno\Programming Projects\Temp Profile Analysis\test_data\dat00002.csv"
UT, LT = 92, -37
ambient_channel_number = 1
tolerance = 3
rate_adjustment = 10

## DATA IMPORT
df, channels, amb, amb_errors = import_data_without_date_index(datapath, ambient_channel_number)
tc_channel_names = ['' for chan in channels]

## PLOT
#plot_profile(TITLE, df, channels)

## ANALYSIS
df = read_data_for_analysis(datapath)
#result_each_cycle_amb, df_summary_amb, ambient= ambient_analysis(df, channels, amb, UT, LT)
#result_each_cycle, df_summary, n_reach_summary =single_channel_analysis(df, channel, ambient, UT, LT, tolerance, rate_adjustment)
analyze_all_channels(df, channels, amb, amb_errors, tc_channel_names, UT, LT)
