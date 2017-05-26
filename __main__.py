#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from core.analysis import *
from core.data_import import *


TEXTFIELD_WIDTH = 3


class ProfileUI(QWidget):

    def __init__(self):
        super().__init__()
        self.test_name = ''
        self.data_file = ''
        self.channels = []
        self.tc_names = []
        self.stylesheet = 'styles\dark.qss'
        self.width = 400
        self.height = 200
        self.init_ui()

    def init_ui(self):
        ## use self.grid layout for GUI
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.setSpacing(10)  # spacing between widgets

        ## data folder
        self.data_file_textfield = QLineEdit('(No Folder Selected)', self)
        self.data_file_button = FileButton('Select Data Folder', self.data_file_textfield, self)
        self.grid.addWidget(self.data_file_button, 0, 0)
        self.grid.addWidget(self.data_file_textfield, 0, 1, 1, TEXTFIELD_WIDTH)

        ## temperature thresholds
        self.upper_temp_label = QLabel('Upper Threshold (\N{DEGREE SIGN}C):', self)
        self.upper_temp_label.setFont(QFont("Times",weight=QFont.Bold))
        self.upper_temp_textfield = QLineEdit(self)
        self.grid.addWidget(self.upper_temp_label, 1, 0)
        self.grid.addWidget(self.upper_temp_textfield, 1, 1, 1, 1)

        self.lower_temp_label = QLabel('Lower Threshold (\N{DEGREE SIGN}C):', self)
        self.lower_temp_label.setFont(QFont("Times",weight=QFont.Bold))
        self.lower_temp_textfield = QLineEdit(self)
        self.grid.addWidget(self.lower_temp_label, 2, 0)
        self.grid.addWidget(self.lower_temp_textfield, 2, 1, 1, 1)

        ## temperature tolerance
        self.temp_tol_label = QLabel('Temperature Tolerance (\N{DEGREE SIGN}C):', self)
        self.temp_tol_textfield = QLineEdit(self)
        self.grid.addWidget(self.temp_tol_label, 3, 0)
        self.grid.addWidget(self.temp_tol_textfield, 3, 1, 1, 1)

        ## threshold component rate adjustment
        self.adjustment_label = QLabel('Component rate adjustment (%):', self)
        self.adjustment_textfield = QLineEdit(self)
        self.grid.addWidget(self.adjustment_label, 4, 0)
        self.grid.addWidget(self.adjustment_textfield, 4, 1, 1, 1)

        ## load tc button
        self.load_tc_button = QPushButton('Load TCs...', self)
        self.grid.addWidget(self.load_tc_button, 5, 0, 1, 4)
        self.load_tc_button.clicked.connect(lambda: self.populate_tc_field_group(6))
        
        ## gui window properties
        self.setStyleSheet(open(self.stylesheet, "r").read())
        self.setWindowTitle('Temperature Profile Analysis')
        self.setWindowIcon(QIcon('images\sine.png'))
        self.resize(self.width, self.height)
        self.move(300, 150) # center window
        self.show()

    def populate_tc_field_group(self, row):
        ''' Populate GUI with user input TC analysis widgets '''
        try:
            self.retrieve_thermocouple_channels()

            ## ambient temp channel field
            self.amb_chan_label = QLabel('Amb Temp Channel:', self)
            self.amb_chan_textfield = QLineEdit(self)
            self.grid.addWidget(self.amb_chan_label, row, 0)
            self.grid.addWidget(self.amb_chan_textfield, row, 1, 1, 1)
            row += 1

            ## thermocouple fields
            for i, channel in enumerate(self.channels):
                self.add_tc_field(i, channel, row)
                row += 1

            ## analyze button
            self.analyze_button = AnalyzeButton('Analyze!', self)
            self.grid.addWidget(self.analyze_button, row, 0, 1, 4)

        except OSError as e: ## no datapath selected
            print('\n', e)
            print('Data load error -- Make sure you have selected a valid data file')

    def retrieve_thermocouple_channels(self):
        datapath = self.data_file_textfield.text()
        df_temp = pd.read_csv(datapath, nrows=5)
        self.channels = get_channels(df_temp)

    def add_tc_field(self, i, channel, row):
        ''' Adds a single TC widget pair to the GUI '''
        label = QLabel(channel+':', self)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        field = QLineEdit(self)
        if i+1 <= 10:
            use_row = row
            column = 0
        else:
            use_row = row-10
            column = 2
        self.grid.addWidget(label, use_row, column)
        self.grid.addWidget(field, use_row, column+1)
        self.tc_names.append(field)

class FileButton(QPushButton):

    def __init__(self, text, text_box, ui):
        super().__init__()
        self.ui = ui
        self.setText(text)
        self.text_box = text_box
        self.name = ''
        self.clicked.connect(self.select_file)

    def select_file(self):
        self.name = str(QFileDialog.getOpenFileName(self, "Select temperature data file")[0])
        self.text_box.setText(self.name)
        self.ui.data_file = self.name
     

class AnalyzeButton(QPushButton):

    def __init__(self, name, ui):
        super().__init__()
        self.init_button(name)
        self.ui = ui

    def init_button(self, name):
        self.setText(name)
        self.name = name
        self.clicked[bool].connect(self.analyze)

    def analyze(self):

        ## Get user inputs
        datapath = self.ui.data_file_textfield.text()
        tolerance = int(self.ui.temp_tol_textfield.text())
        upper_threshold = int(self.ui.upper_temp_textfield.text())
        lower_threshold = int(self.ui.lower_temp_textfield.text())
        ambient_channel_number = convert_channel_to_num(self.ui.amb_chan_textfield.text())
        rate_adjustment = self.ui.adjustment_textfield.text()
        title = 'Temperature Profile Analysis'

        if rate_adjustment:
            rate_adjustment = float(self.ui.adjustment_textfield.text())/100.0

        ## Load TC component/location name labels
        tc_channel_names = {}  ## key: channel, value: tc_name
        for i, channel in enumerate(self.ui.channels):
            tc_channel_names[channel] = self.ui.tc_names[i].text()

        ### Print test parameters
        print('Datapath:', datapath)
        print('Upper Threshold:', upper_threshold)
        print('Lower Threshold:', lower_threshold)
        print('Channels:', tc_channel_names)

        ## if all required user inputs exist
        if datapath and upper_threshold and lower_threshold and ambient_channel_number and isinstance(tolerance, int):
            ### Do plot
            #df, channels, amb, errors = import_data_with_date_index(datapath, ambient_channel_number)  ## df time indexed
            #plot_profile(title, df, channels, tc_channel_names)  ## plot with ploty
            
            ### Do analysis
            df, channels, amb, amb_errors = import_data_without_date_index(datapath, ambient_channel_number) ## df raw for analysis
            analyze_all_channels(df, channels, amb, amb_errors, tc_channel_names, upper_threshold, lower_threshold, tolerance, rate_adjustment)
        else:
            print('\n', 'All user inputs must be filled before analysis can be conducted. Please fill in the required fields.')


### TC conversion helper
def convert_channel_to_num(channel_number):
    ''' Channel_number input is a  string '''
    if len(channel_number) > 1:
        chan_num = int(channel_number[-2:])
    elif len(channel_number) == 1:
        chan_num = int(channel_number)
    else:
        chan_num = 1
    return chan_num



if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    gui = ProfileUI()
    sys.exit(app.exec_())
