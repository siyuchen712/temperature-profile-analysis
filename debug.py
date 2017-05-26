
from core.ambient import *
from core.data_import import *



datapath = r"C:\Users\bruno\Programming Projects\Temp Profile Analysis\test_data\dat00002.csv"
UT, LT = 92, -37
ambient_channel_number = 1

## DATA IMPORT
df, channels, amb, errors = import_data(datapath, ambient_channel_number)

## PLOT
#plot_profile(TITLE, df, channels)

## ANALYSIS
df = read_data_for_analysis(datapath)
result_each_cycle, df_summary, ambient = ambient_analysis(df, channels, amb, UT, LT)
#analyze_all_channels(df, channels, amb)
