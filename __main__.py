#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

TEXTFIELD_WIDTH = 3


class ProfileUI(QWidget):

    def __init__(self):
        super().__init__()
        self.test_name = ''
        self.data_file = ''
        self.number_of_channels = 15
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

        ## load tc button
        self.load_tc_button = QPushButton('Load TCs...', self)
        self.grid.addWidget(self.load_tc_button, 4, 0, 1, 4)
        self.load_tc_button.clicked.connect(lambda: self.populate_tc_field_group(5, self.number_of_channels))
        
        ## gui window properties
        self.setStyleSheet(open(self.stylesheet, "r").read())
        self.setWindowTitle('Temperature Profile Analysis')
        self.setWindowIcon(QIcon('images\sine.png'))
        self.resize(self.width, self.height)
        self.move(300, 150) # center window
        self.show()

    def populate_tc_field_group(self, row, number_of_channels):
        ''' Populate GUI with user input TC analysis widgets '''
        self.amb_chan_label = QLabel('Amb Temp Channel:', self)
        self.amb_chan_textfield = QLineEdit(self)
        self.grid.addWidget(self.amb_chan_label, row, 0)
        self.grid.addWidget(self.amb_chan_textfield, row, 1, 1, 1)
        row += 1

        self.adjustment_label = QLabel('Component rate adjustment (%):', self)
        self.adjustment_textfield = QLineEdit(self)
        self.grid.addWidget(self.adjustment_label, row, 0)
        self.grid.addWidget(self.adjustment_textfield, row, 1, 1, 1)
        row += 1

        for channel in range(1, number_of_channels+1):
            self.add_tc_field(channel, row)
            row += 1
        self.analyze_button = AnalyzeButton('Analyze!', self)
        self.grid.addWidget(self.analyze_button, row, 0, 1, 4)

    def add_tc_field(self, channel, row):
        '''  Adds a single TC widget pair to the GUI '''
        label = QLabel('Channel '+str(channel)+':', self)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        field = QLineEdit(self)
        if channel <= 10:
            use_row = row
            column = 0
        else:
            use_row = row-10
            column = 2
        self.grid.addWidget(label, use_row, column)
        self.grid.addWidget(field, use_row, column+1)


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
        print('Data Folder:', self.ui.data_file_textfield.text())
        print('Upper Thresh:', self.ui.upper_temp_textfield.text())
        print('Lower Thresh:', self.ui.lower_temp_textfield.text())
        print('Tolerance:', self.ui.temp_tol_textfield.text())
        print('Amb Temp Chan:', self.ui.amb_chan_textfield.text())
        print('Rate adjustment:', self.ui.adjustment_textfield.text())


if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    gui = ProfileUI()
    sys.exit(app.exec_())
