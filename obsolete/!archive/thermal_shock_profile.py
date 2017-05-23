import re
import matplotlib.pyplot as plt
import pylab
import numpy
import operator

class TempProfile(object):
    """
    Temp profile data file with time and temperature (amb/product) measurements
    """
    def __init__(self, tempfile):
        self.tempfile = tempfile  # filepath and name of board txt data file
        #self.name = re.findall(r'20[0-9][0-9].+txt', self.boardfile)[0]  # name of board txt data file
        self.f = ''        # a file
        self.header = []   # list of the headers at top of data file
        self.times = []    # list of times of scans
        self.temps = {}    # dict of temperature t.c. data
        self.num_tc = 0    # int representing the number of thermocouples used
        self.channels = []   # channels used on agilent for t.c. data
        self.scan_rt = None  # int scan rate
        self.minutes = []    # time in minutes

    def openFile(self):
        '''
        Opens the board file for reading
        '''
        try:
            self.f = open(self.tempfile, 'r')
        except IOError as e:
            print(e)

    def getTempFile(self):
        return self.tempfile

    def getName(self):
        return self.name

    def getTimes(self):
        return self.times

    def getTemps(self):
        return self.temps

    def getNumTC(self):
        return self.num_tc

    def getChannels(self):
        return self.channels

    def getScanRate(self):
        '''
        Calculates scan rate from data and returns scan_rt as int
        '''
        if self.scan_rt == None:
            t1 = int(self.getTimes()[0][-6:-4])   # seconds at first scan
            t2 = int(self.getTimes()[1][-6:-4])   # seconds at second scan
            self.scan_rt = t2 - t1
            if t1 > t2:
                self.scan_rt += 60
        return self.scan_rt

    def getMinutes(self):
        return self.minutes

    def getHeader(self):
        '''
        Get header of temp dat file and return as list
        '''
        if self.header == []:
            self.f.seek(0,0)  # start at beginning of file
            self.header = self.f.readline().split(',')
            #header[len(header)-1] = header[len(header)-1][0:-1]
        return self.header

    def getCol(self, col):
        '''
        Get specified column from board and return as list
        input = column header string
        output  = column as list
        '''
        self.f.seek(0,0)    # start at beginning of file
        self.f.readline()   # skip header
        data = []
        try:
            i = self.getHeader().index(col)
            for line in self.f:
                columns = line.split(',')
                data.append(columns[i].replace('\n',''))
            return data
        except ValueError as e:
            print(e)

    def getTempCol(self, col):
        '''
        Get specified column from board and return as list
        input = column header string
        output  = column as list
        '''
        self.f.seek(0,0)    # start at beginning of file
        self.f.readline()   # skip header
        data = []
        try:
            i = self.getHeader().index(col)
            for line in self.f:
                columns = line.split(',')
                data.append(float(columns[i].replace('\n','')))
            return data
        except ValueError as e:
            print(e)

    def allocateData(self):
        '''
        Extract and organize data from temp file
        '''
        self.openFile()
        self.times = self.getCol('Time')
        #self.getScanRate()
        self.minutes = [t / 60.0 for t in [T * self.getScanRate() for T in range(len(self.getTimes()))]]  # make x-axis minutes w/ correct scan rate
        for h in self.getHeader():
            if re.search('^Chan [0-9].+', h):
                channel = int(re.findall('^Chan [0-9]([0-9][0-9]).+', h)[0])
                self.temps[channel] = self.getTempCol(h)
        self.num_samples = len(self.temps)
        self.channels = self.temps.keys()

###### plotting functions
def graph1(path, title = 'Thermal Shock Temperature Profile'):
    """
    Plotting function for temps vs. time.
    profile (input) = temp profile object
    """
    profile = TempProfile(path)
    x = profile.getMinutes()
    data = profile.getTemps()
    pylab.figure(1)
    for key in data.keys():
        pylab.plot (x, data[key], label='Ch'+str(key))
    pylab.xlabel('Time (min)', fontsize = 'large')
    pylab.ylabel('Temperature (C)', fontsize = 'large')
    pylab.title(title, fontsize = 30)
    pylab.legend(bbox_to_anchor=(.99, .99), bbox_transform=pylab.gcf().transFigure,fontsize='large')
    pylab.grid(True)
    pylab.show()

def plot1(path, title = 'Thermal Shock Temperature Profile'):
    """
    Plotting function for temps vs. time.
    profile (input) = temp profile object
    """
    profile = TempProfile(path)
    x = profile.getMinutes()
    data = profile.getTemps()
    plt.figure(1)
    for channel in data.keys():
        plt.plot(x, data[channel], label='Ch'+str(channel))
    plt.xlabel('Time (min)', fontsize = 'large')
    plt.ylabel('Temperature (C)', fontsize = 'large')
    plt.title(title, fontsize = 30)
    plt.legend(bbox_to_anchor=(.99, .99), bbox_transform=plt.gcf().transFigure,fontsize='large')
    plt.grid(True)
    plt.show()

def findEdges(profile, entrance, threshold, op):
    """
    Finds edges of temp profile given for given threshold and operator
    threshold: number temperature
    entrance: True/False (an entrance/exit to a soak)
    op: '<' '>' '<=' '>=' or '=='
    Returns dictionary of channel t.c. keys into (Time, Temp) tuple data """

    op_map = {'<': operator.lt, '<=': operator.le, '>': operator.gt, '>=': operator.ge, '==': operator.eq}
    times = profile.getMinutes()
    data = profile.getTemps()
    channels = profile.getChannels()
    edges = {}
    for chan in channels:
        edges[chan] = []
        signal = numpy.array(data[chan])
        thresholded_data = op_map[op](signal, threshold)
        threshold_edges = numpy.convolve([1, -1], thresholded_data, mode='same')
        thresholded_edge_indices = numpy.where(threshold_edges==1)[0]
        for i in thresholded_edge_indices:
            if entrance:
                tmp_edge = (times[i], signal[i])
            else:  # go back one time scan for soak exits
                tmp_edge = (times[i-1], signal[i-1])
            if times[i] != 0.0 and edges[chan] == []:   ## add data point if
                edges[chan].append(tmp_edge)
            ## only add data point if difference between current time and last entry is greater than 50 min
            elif edges[chan] != [] and abs(tmp_edge[0] - edges[chan][-1][0]) > 50:
                edges[chan].append(tmp_edge)
    return edges

def byCycles(data):
    """
    Reorganizes soak or ramp rate data by cycles instead of TC channels
    """
    byCycleData = {}
    channels = sorted(data.keys())

    ## find longest number of cycles
    cycles = 0
    for chan in channels:
        length = len(data[chan])
        if length > cycles:
            cycles = length
    for i in range(cycles):
        byCycleData[i+1] = []
        for chan in channels:
            try:
                byCycleData[i+1].append(data[chan][i])
            except IndexError:
                byCycleData[i+1].append('DNR')
    return byCycleData

def printStats(title, data, channels):
    """
    Prints out profile data stats (hot/cold soaks and ramp ups/downs) by cycle
    """
    h = '======================================'
    cycles = sorted(data.keys())
    print(h, title, h)
    print('\t\t',)
    for chan in channels:
        print('TC' + str(chan) + '\t',)
    print('')
    for cyc in cycles:
        print('Cycle', cyc, '\t',)
        for i in range(len(data[cyc])):
            print(data[cyc][i], '\t',)
        print('')
    print(2*'------------------------------------------------')

def printAvgs(data, channels):
    """
    Prints out avgs of temp profile data
    """
    h = '------------------------------------------------'
    print('\t\t',)
    for chan in channels:
        print('TC' + str(chan) + '\t',)
    print('')
    print('Average:', '\t',)
    for chan in channels:
        print(data[chan], '\t',)
    print('\n', 2*h, '\n')

def writeStats(f, title, data, channels):
    """
    Writes profile data stats (hot/cold soaks and ramp ups/downs) by cycle
    to file
    """
    h = '=============================================='
    cycles = sorted(data.keys())
    f.write(str(h) + str(title) + str(h) + '\n')
    f.write('\t')
    for chan in channels:
        f.write('TC' + str(chan) + '\t')
    f.write('\n')
    for cyc in cycles:
        f.write('Cycle ' + str(cyc) + ' \t')
        for i in range(len(data[cyc])):
            f.write(str(data[cyc][i]) + ' \t')
        f.write('\n')
    f.write(2*'----------------------------------------------------------------------')
    f.write('\n')

def writeAvgs(f, data, channels):
    """
    Writes avgs of temp profile data to file
    """
    h = '----------------------------------------------------------------------'
    f.write('\t')
    for chan in channels:
        f.write('TC' + str(chan) + '\t')
    f.write('\n')
    f.write('Average: \t')
    for chan in channels:
        f.write(str(data[chan]) + ' \t')
    f.write('\n' + str(2*h) + '\n\n')

def getAvgs(data):
    """
    Calculate avg soak and ramp data and return as channel-keyed dict
    """
    avgs = {}
    channels = sorted(data.keys())
    for chan in channels:
        length = len(data[chan])
        total = 0
        if length == 0:
            avgs[chan] = 'NA'
        else:
            for e in data[chan]:
                if type(e) == float:
                    total += e
            avgs[chan] = round(total/float(length), 2)
    return avgs

def analyze(profile):
    """
    Analyzes temperature profile -- soaks and rate changes.
    profile (input) = temp profile object """

    hot_soaks = {}
    cold_soaks = {}
    ramp_ups = {}
    ramp_downs = {}

    channels = profile.getChannels()

    enterHot = findEdges(profile, True, 92, '>=')
    exitHot = findEdges(profile, False, 92, '<=')
    enterCold = findEdges(profile, True, -37, '<=')
    exitCold = findEdges(profile, False, -37, '>=')

    tc = 10
    hi = 0
    low = 5
    print('\n')
    print('**************** CHANNEL', tc, ':  Cycles', hi, 'to', low-1, '****************\n')
    print('#### Enter Hot, length:', len(enterHot[tc]), '#### \n', enterHot[tc][hi:low], '\n')
    print('#### Exit Hot, length:', len(enterHot[tc]), '#### \n', exitHot[tc][hi:low], '\n')
    print('#### Enter Cold, length:', len(enterHot[tc]), '#### \n', enterCold[tc][hi:low], '\n')
    print('#### Exit Cold, length:', len(enterHot[tc]), '#### \n', exitCold[tc][hi:low], '\n')
    print('\n')

    for chan in channels:  ## create soak and ramp data organized by channel
        hot_soaks[chan] = []
        cold_soaks[chan] = []
        ramp_ups[chan] = []
        ramp_downs[chan] = []

        # hot soaks
        for i in range(len(enterHot[chan])):
            try:
                if (exitHot[chan][i][0] > enterHot[chan][i][0]):
                    hot_soaks[chan].append(round(exitHot[chan][i][0]-enterHot[chan][i][0], 2))
                else:
                    hot_soaks[chan].append(round(exitHot[chan][i+1][0]-enterHot[chan][i][0], 2))
            except IndexError:
                continue
        # cold soaks
        for i in range(len(enterCold[chan])):
            try:
                if (exitCold[chan][i][0] > enterCold[chan][i][0]):
                    cold_soaks[chan].append(round(exitCold[chan][i][0]-enterCold[chan][i][0], 2))
                else:
                    cold_soaks[chan].append(round(exitCold[chan][i+1][0]-enterCold[chan][i][0], 2))
            except IndexError:
                continue
        # ramp up rates
        for i in range(len(exitCold[chan])):
            try:
                if (enterHot[chan][i][0] > exitCold[chan][i][0]):
                    ramp_ups[chan].append(round((enterHot[chan][i][1]-exitCold[chan][i][1])/(enterHot[chan][i][0]-exitCold[chan][i][0]), 2))
                else:
                    ramp_ups[chan].append(round((enterHot[chan][i+1][1]-exitCold[chan][i][1])/(enterHot[chan][i+1][0]-exitCold[chan][i][0]), 2))
            except IndexError:
                continue
        # ramp down rates
        for i in range(len(exitHot[chan])):
            try:
                if (enterCold[chan][i][0] > exitHot[chan][i][0]):
                    ramp_downs[chan].append(round((enterCold[chan][i][1]-exitHot[chan][i][1])/(enterCold[chan][i][0]-exitHot[chan][i][0]), 2))
                else:
                    ramp_downs[chan].append(round((enterCold[chan][i+1][1]-exitHot[chan][i][1])/(enterCold[chan][i+1][0]-exitHot[chan][i][0]), 2))
            except IndexError:
                continue

    hot_avgs = getAvgs(hot_soaks)
    cold_avgs = getAvgs(cold_soaks)
    up_avgs = getAvgs(ramp_ups)
    down_avgs = getAvgs(ramp_downs)

    cyc_hot = byCycles(hot_soaks)
    cyc_cold = byCycles(cold_soaks)
    cyc_up = byCycles(ramp_ups)
    cyc_down = byCycles(ramp_downs)

    printStats('Hot Soaks (min)', cyc_hot, channels)
    printAvgs(hot_avgs, channels)
    printStats('Cold Soaks (min)', cyc_cold, channels)
    printAvgs(cold_avgs, channels)
    printStats(u'Ramp Ups (\N{DEGREE SIGN}C/min)', cyc_up, channels)
    printAvgs(up_avgs, channels)
    printStats(u'Ramp Downs (\N{DEGREE SIGN}C/min)', cyc_down, channels)
    printAvgs(down_avgs, channels)

    return profile.tempfile, cyc_hot, cyc_cold, cyc_up, cyc_down, hot_avgs, cold_avgs, up_avgs, down_avgs, channels

def writeFile(path):
    profile = TempProfile(path)
    profile.allocateData()
    data = analyze(profile)

    title = data[0]
    cyc_hot = data[1]
    cyc_cold = data[2]
    cyc_up = data[3]
    cyc_down = data[4]
    hot_avgs = data[5]
    cold_avgs = data[6]
    up_avgs = data[7]
    down_avgs = data[8]
    channels = data[9]

    f = open("tshock_analysis.txt", 'w')
    f.write(str(title) + '\n\n\n')
    writeStats(f, 'Hot Soaks (min)', cyc_hot, channels)
    writeAvgs(f, hot_avgs, channels)
    writeStats(f, 'Cold Soaks (min)', cyc_cold, channels)
    writeAvgs(f, cold_avgs, channels)
    writeStats(f, 'Ramp Ups (degC/min)', cyc_up, channels)
    writeAvgs(f, up_avgs, channels)
    writeStats(f, 'Ramp Downs (degC/min)', cyc_down, channels)
    writeAvgs(f, down_avgs, channels)

    f.close()

def writeAndPlot(path):
    writeFile(path)
    plot1(path)


### Testing ###
path = r"\\Chfile1\ecs_landrive\Automotive_Lighting\LED\P552 MCA Headlamp\P552 MCA Aux\ADVPR\PV Aux\TL D\Agilent Temperature Data\20000217_235248186\dat00001.csv"

plot1(path)
#writeAndPlot(path)
#writeFile(r"\\chfile1\ecs_landrive\Automotive_Lighting\LED\P558\ADVPR\PV Aux\Test Leg D Thermal Shock Endurance\Thermal Shock Endurance Test\Raw Data Cycles 501-1000\20151226_145207868\dat00001.csv")
#writeFile(r"\\Chfile1\ecs_landrive\Automotive_Lighting\LED\P552 MCA Headlamp\P552 MCA Aux\ADVPR\PV Aux\TL D\Agilent Temperature Data\20000217_235248186\dat00001.csv")
