import re
import pandas as pd
import operator
from helper_functions import *

REGEX_TEMP_COL = '^Chan\s[0-9][0-9][0-9]'
parse_datetime = lambda x: pd.datetime.strptime(x, '%m/%d/%Y %H:%M:%S:%f')  ## parsing function for datetime dataframes

class TempProfile(object):
    ''' Temp profile data file with time and temperature (amb/product) measurements '''
    def __init__(self, tempfile, cycle_time):
        self.tempfile = tempfile  # filepath and name of temperature csv data file
        self.cycle_time = cycle_time # cycle time in minutes

        self.start_time = ''  # start time of thermal profile test
        self.df = pd.DataFrame()  # df to hold csv data
        self.channels = []  # TC channels
        self.sweep_col = ['Sweep #']  # sweep number column header
        self.edges = {}  # channel -> edge_type -> time/temp tuple
                         # edges[channel][edge_type](time, temp)

    def buildDataframe(self):
        ''' Builds dataframe from Agilent temperature csv file '''
        print('\nBuilding dataframe...')
        try:
            self.df = pd.read_csv(self.tempfile, date_parser=parse_datetime,
                                  index_col='Time', sep=',', engine='python',
                                  usecols=range(22))
            # self.df.index = self.df.index.map(lambda t: t.strftime('%Y-%m-%d %H:%M:%S'))
            self.channels = [self.df.columns[i] for i in range(len(self.df.columns)) if re.search(REGEX_TEMP_COL, self.df.columns[i])]
            self.start_time = self.df.first_valid_index()  ## set start_time to timestamp of first scan
        except Exception:
            print('The following error occurred while attempting to convert the ' \
                  'temperature data file to a dataframe:\n\n')
            raise
        print('...complete.')

    def buildEdges(self):
        print('Scanning for profile edges...')
        for channel in self.channels:
            series = self.df[channel]
            self.edges[channel] = ChannelEdges(series, channel, self.cycle_time,
                                               start_time= self.start_time)
            self.edges[channel].findProfileEdges()
            print('Channel', channel, 'complete.')

    def printAllEdges(self):
        for channel in self.channels:
            print('*****CHANNEL', channel, '*****')
            self.edges[channel].printChannelEdges()

    def printRampUpRates(self):
        for channel in self.channels:
            print('\n*****CHANNEL', channel, '*****')
            self.edges[channel].calculateRampUpRates()

    def printRampDownRates(self):
        for channel in self.channels:
            print('\n*****CHANNEL', channel, '*****')
            self.edges[channel].calculateRampDownRates()

class ChannelEdges(object):
    ''' Creates edges object that holds time/temp data for hot/cold entrance/exit
        events for a single TC channel '''

    HOT_THRESHOLD = 92
    COLD_THRESHOLD = -37

    def __init__(self, series, channel, cycle_time, start_time):
        self.series = series  # col channel data
        self.channel = channel  # col string name, e.g. - 'Chan 101 (C)'
        self.cycle_time = cycle_time
        self.start_time = start_time

        self.hot_entrances = []
        self.hot_exits = []
        self.cold_entrances = []
        self.cold_exits = []

    def isHotEntrance(self, last_temp, current_temp, next_temp, threshold):
        ''' Returns True/False whether entering hot soak '''
        return (last_temp < threshold) and \
               (current_temp > threshold) and (next_temp > threshold)

    def isHotExit(self, last_temp, current_temp, next_temp, threshold):
        ''' Returns True/False whether exiting hot soak '''
        return (last_temp > threshold) and \
               (current_temp > threshold) and (next_temp < threshold)

    def isColdEntrance(self, last_temp, current_temp, next_temp, threshold):
        ''' Returns True/False whether entering cold soak '''
        return (last_temp > threshold) and \
               (current_temp < threshold) and (next_temp < threshold)

    def isColdExit(self, last_temp, current_temp, next_temp, threshold):
        ''' Returns True/False whether exiting cold soak '''
        return (last_temp < threshold) and \
               (current_temp < threshold) and (next_temp > threshold)

    def saveEdge(self, edge_list, index, temp):
        ''' Saves edge object into input edge_list '''
        time_into_test = ((index-self.start_time).total_seconds())/60
        ## if list is empty, then append edge
        if (not edge_list):
            edge_list.append(Edge(index, temp, time_into_test))
        ## elif time diff of this edge and last edge is less than 50% cycle time, then replace
        elif (time_into_test - edge_list[-1].time_into_test) < (0.5*self.cycle_time):
            edge_list[-1] = Edge(index, temp, time_into_test)
        ## elif time diff is 2 cycles or greater, then add some 'DNR' (did not reach) data
        elif (time_into_test - edge_list[-1].time_into_test) > (1.5*self.cycle_time):
            number_of_missing_cycles = round((time_into_test - edge_list[-1].time_into_test)/self.cycle_time) - 1
            edge_list.extend( [Edge('no time', 'DNR', 'DNR') for i in range(number_of_missing_cycles)] )
            edge_list.append(Edge(index, temp, time_into_test))
        ## otherwise append edge
        else:
            edge_list.append(Edge(index, temp, time_into_test))

    def findProfileEdges(self, hot_threshold=HOT_THRESHOLD, cold_threshold=COLD_THRESHOLD):
        ''' Finds the profile edges for single thermocouple channel '''
        df = pd.DataFrame({self.channel: seseries})  ## expand TC channel series into a df
        df['last'] = self.series.shift(1)  ## create column of previous (last) scan
        df['next'] = self.series.shift(-1)  ## create column of next scan
        i, j, k, l = 1, 1, 1, 1
        for index, row in df.iterrows():  ## for each row in dataframe
            temp, next_temp, last_temp = row[self.channel], row['next'], row['last']
            if self.isHotEntrance(last_temp, temp, next_temp, hot_threshold):
                self.saveEdge(self.hot_entrances, index, temp)
            elif self.isHotExit(last_temp, temp, next_temp, hot_threshold):
                self.saveEdge(self.hot_exits, index, temp)
            elif self.isColdEntrance(last_temp, temp, next_temp, cold_threshold):
                self.saveEdge(self.cold_entrances, index, temp)
            elif self.isColdExit(last_temp, temp, next_temp, cold_threshold):
                self.saveEdge(self.cold_exits, index, temp)

    def printChannelEdges(self):
        print('HOT ENTRANCES')
        for edge in self.hot_entrances:
            edge.printEdge()
        print('HOT EXITS')
        for edge in self.hot_exits:
            edge.printEdge()
        print('COLD ENTRANCES')
        for edge in self.cold_entrances:
            edge.printEdge()
        print('COLD EXITS')
        for edge in self.cold_exits:
            edge.printEdge()

    def calculateRampUpRates(self):
        number_of_detected_edges = shorterLengthOf(self.cold_exits, self.hot_entrances)
        for i in range(number_of_detected_edges):
            time_diff = self.hot_entrances[i].time_into_test - self.cold_exits[i].time_into_test
            temp_diff = self.hot_entrances[i].temperature - self.cold_exits[i].temperature
            ramp_rate = temp_diff / time_diff
            print(i+1, '\tRamp Rate:', ramp_rate)
            print('\tCold Exit Time:', round(self.cold_exits[i].time_into_test,1),
                  '\tTimestamp:', self.cold_exits[i].time)
            print('\tHot Entrance Time:', round(self.hot_entrances[i].time_into_test,1),
                  '\tTimestamp:', self.hot_entrances[i].time)

    def calculateRampDownRates(self):
        number_of_detected_edges = shorterLengthOf(self.hot_exits, self.cold_entrances)
        for i in range(number_of_detected_edges):
            time_diff = self.cold_entrances[i].time_into_test - self.hot_exits[i].time_into_test
            temp_diff = self.cold_entrances[i].temperature - self.hot_exits[i].temperature
            ramp_rate = temp_diff / time_diff
            print(i+1, '\tRamp Rate:', round(ramp_rate,1))
            print('\tHot Exit Time:', round(self.hot_exits[i].time_into_test,1),
                  '\n\tTimestamp:', self.hot_exits[i].time)
            print('\tCold Entrance Time:', round(self.cold_entrances[i].time_into_test,1),
                  '\n\tTimestamp:', self.cold_entrances[i].time)

    def calculateSoak(self):
        pass


class Edge(object):
    ''' An object holding time, temperature, time into test of profile edge '''
    def __init__(self, time, temperature, time_into_test):
        # self.cycle_number = cycle_number
        self.time = time
        self.temperature = temperature
        self.time_into_test = time_into_test

    def printEdge(self):
        print('\tTime:', self.time_into_test, '\tTemp:', self.temperature)
