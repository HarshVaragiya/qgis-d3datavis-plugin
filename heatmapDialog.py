import os
import re
import dateutil.parser
from shutil import copyfile

from PyQt4 import uic, QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'heatmapdialog.ui'))

OPTIONMENU = ['Year', 'Month', 'Day of Month', 'Day of Week', 'Hour of Day']

class AutoDict(dict):
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] =  type(self)()
        return value
    def __iadd__(self, item):
        return item
        
class HeatmapDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, iface, parent):
        super(HeatmapDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.layerComboBox.activated.connect(self.userSelectsLayer)
        self.dtRadioButton.clicked.connect(self.enableComponents)
        self.notdtRadioButton.clicked.connect(self.enableComponents)
        self.okButton.clicked.connect(self.createChart)
        self.closeButton.clicked.connect(self.close)
        self.radialComboBox.addItems(OPTIONMENU)
        self.circleComboBox.addItems(OPTIONMENU)

        
    def showEvent(self, event):
        super(HeatmapDialog, self).showEvent(event)
        self.populateLayerListComboBox()
    
    def populateLayerListComboBox(self):
        layerlist = []
        self.foundLayers = [] # This is same size as layerlist
        layers = self.iface.legendInterface().layers()
        
        for layer in layers:
            if isinstance(layer, QgsVectorLayer):
                layerlist.append(layer.name())
                self.foundLayers.append(layer)

        self.layerComboBox.clear()
        self.layerComboBox.addItems(layerlist)
        self.initLayerFields()
    
    def userSelectsLayer(self):
        self.initLayerFields()
        
    def initLayerFields(self):
        self.dtComboBox.clear()
        self.dateComboBox.clear()
        self.timeComboBox.clear()
        self.dtRadioButton.setChecked(True)
        if len(self.foundLayers) == 0:
            return
        selectedLayer = self.layerComboBox.currentIndex()
        for field in self.foundLayers[selectedLayer].pendingFields():
            self.dtComboBox.addItem(field.name())
            self.dateComboBox.addItem(field.name())
            self.timeComboBox.addItem(field.name())
        self.enableComponents()
    
    def enableComponents(self):
        if self.dtRadioButton.isChecked():
            self.dtComboBox.setEnabled(True)
            self.dateComboBox.setEnabled(False)
            self.timeComboBox.setEnabled(False)
        else:
            self.dtComboBox.setEnabled(False)
            self.dateComboBox.setEnabled(True)
            self.timeComboBox.setEnabled(True)
        
    def readChartParams(self):
        self.selectedLayer = self.foundLayers[self.layerComboBox.currentIndex()]
        self.selectedDateTimeCol = self.dtComboBox.currentIndex()
        self.selectedDateCol = self.dateComboBox.currentIndex()
        self.selectedTimeCol = self.timeComboBox.currentIndex()
        self.selectedRadialUnit = self.radialComboBox.currentIndex()
        self.selectedCircleUnit = self.circleComboBox.currentIndex()
        self.showRadialLabels = self.radialLabelCheckBox.isChecked()
        self.showBandLabels = self.bandLabelCheckBox.isChecked()
        self.chartTitle = unicode(self.titleEdit.text())
        self.showDataValues = self.showValuesCheckBox.isChecked()
        self.dataValueLabel = unicode(self.dataValueLabelEdit.text())
        try:
            self.chartInnerRadius = int(self.innerRadiusEdit.text())
        except:
            # Need a valid exception error
            self.chartInnerRadius = 25
            self.innerRadiusEdit.setText('25') # Set it to the default value
        try:
            self.chartBandHeight = int(self.bandHeightEdit.text())
        except:
            self.chartBandHeight = 16
            self.bandHeightEdit.setText('16')

    def parseDateTimeValues(self, requestedField, dt, time=None):
        '''This returns the requested date or time value from a datetime
           date only and/or time only field. Note that it can throw an exception.'''
        if isinstance(dt, QDate):
            if requestedField == 0: # Year
                return dt.year()
            elif requestedField == 1: # Month
                return dt.month()
            elif requestedField == 2: # Day
                return dt.day()
            elif requestedField == 3: # Day of Week
                return dt.dayOfWeek() - 1
                
        if isinstance(dt, QDateTime):
            if requestedField == 0: # Year
                return dt.date().year()
            elif requestedField == 1: # Month
                return dt.date().month()
            elif requestedField == 2: # Day
                return dt.date().day()
            elif requestedField == 3: # Day of Week
                return dt.date().dayOfWeek() - 1
            elif requestedField == 4 and time is None:
                return dt.time().hour()
        
        if requestedField == 4 and time is not None:
            if isinstance(time, QTime):
                return time.hour()
            elif isinstance(time, QDateTime):
                return time.time().hour()
            else:
                d = dateutil.parser.parse(time)
                return d.hour
                
        d = dateutil.parser.parse(dt)
        if requestedField == 0:
            return d.year
        elif requestedField == 1:
            return d.month
        elif requestedField == 2:
            return d.day
        elif requestedField == 3:
            return d.weekday()
        else:
            return d.hour
        # Not sure if we will ever reach this point, but if so throw an exception
        raise ValueError('Improper date or time')
                
    def createChart(self):
        if len(self.foundLayers) == 0:
            return
        self.readChartParams()
        folder = askForFolder(self)
        if not folder:
            return
        
        data   = AutoDict()
        rvlist = AutoDict()
        cvlist = AutoDict()
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)
        isdt = self.dtRadioButton.isChecked()
        if isdt:
            request.setSubsetOfAttributes([self.selectedDateTimeCol])
        else:
            request.setSubsetOfAttributes([self.selectedDateCol, self.selectedTimeCol])
        
        iter = self.selectedLayer.getFeatures(request)
        for f in iter:
            try:
                if isdt:
                    rv = self.parseDateTimeValues(self.selectedRadialUnit, f[self.selectedDateTimeCol])
                    cv = self.parseDateTimeValues(self.selectedCircleUnit, f[self.selectedDateTimeCol])
                else:
                    rv = self.parseDateTimeValues(self.selectedRadialUnit, f[self.selectedDateCol], f[self.selectedTimeCol])
                    cv = self.parseDateTimeValues(self.selectedCircleUnit, f[self.selectedDateCol], f[self.selectedTimeCol])
            except:
                continue
            
            rvlist[rv] += 1
            cvlist[cv] += 1
            data[rv][cv] += 1
        if not any(cvlist) or not any(rvlist):
            self.iface.messageBar().pushMessage("", "Valid dates were not found" , level=QgsMessageBar.WARNING, duration=3)
            return
        rvmin, rvmax, rvunits = self.getUnitStr(rvlist, self.selectedRadialUnit)
        cvmin, cvmax, cvunits = self.getUnitStr(cvlist, self.selectedCircleUnit)
        if rvunits is None or cvunits is None:
            self.iface.messageBar().pushMessage("", "There is too large of a year range to create chart" , level=QgsMessageBar.WARNING, duration=3)
            return
        datastr = self.formatData(data, rvmin, rvmax, cvmin, cvmax)
        
        segCnt = rvmax-rvmin+1
        bandCnt = cvmax-cvmin+1
        chartSize = self.chartInnerRadius*2 + (bandCnt + 1)*2*self.chartBandHeight + 10 # 10 is additional margin
        style = '#chart svg {{\n\theight: {}px;\n\twidth: {}px;\n}}'.format(chartSize, chartSize)
        script = []
        script.append('var segHeight={};'.format(self.chartBandHeight))
        script.append('var segCnt={};'.format(segCnt))
        script.append('var bandCnt={};'.format(bandCnt))
        script.append('var segLabels={};'.format(rvunits))
        script.append('var bandLabels={};'.format(cvunits))
        script.append('var innerRadius={};'.format(self.chartInnerRadius))
        script.append('var edata=[{}];'.format(datastr))
        rl = ''
        if self.showRadialLabels:
            rl = '\n\t.segmentLabels(segLabels)'
        bl = ''
        if self.showBandLabels:
            bl = '\n\t.radialLabels(bandLabels)'
        script.append('var chart = circularHeatChart()\n\t.segmentHeight(segHeight)\n\t.innerRadius(innerRadius)\n\t.numSegments(segCnt){}{};'
                .format(rl, bl))
        script.append('d3.select(\'#chart\')\n\t.selectAll(\'svg\')\n\t.data([edata])\n\t.enter()\n\t.append(\'svg\')\n\t.call(chart);')
        
        if self.showDataValues:
            script.append('d3.selectAll("#chart path").on(\'mouseover\', function() {\n\tvar d = d3.select(this).data();\n\td3.select("#info").text(\'' +
                self.dataValueLabel + ' \' + d);\n});')

        values = {"@TITLE@": self.chartTitle,
                "@STYLE@": style,
                "@SCRIPT@": '\n'.join(script)
            }
        template = os.path.join(os.path.dirname(__file__), "templates", "index.html")
        html = replaceInTemplate(template, values)
        
        filename = os.path.join(folder, "index.html")
        try:
            fout = open(filename, 'w')
        except:
            self.iface.messageBar().pushMessage("", "Error opening output file" , level=QgsMessageBar.CRITICAL, duration=3)
            return
        fout.write(html)
        fout.close()
        #Copy over the d3 libraries
        copyfile(os.path.join(os.path.dirname(__file__), "d3", "d3.min.js"), 
            os.path.join(folder,"d3.min.js"))
        copyfile(os.path.join(os.path.dirname(__file__), "d3", "circularHeatChart.js"), 
            os.path.join(folder,"circularHeatChart.js"))
        QMessageBox().information(self, "Date Time Heatmap", "Chart has been created")
    
    def formatData(self, data, rvmin, rvmax, cvmin, cvmax):
        datastrs=[]
        for x in range(cvmin, cvmax+1):
            for y in range(rvmin, rvmax+1):
                if not data[y][x]:
                    datastrs.append('0')
                    #datastrs.append('')
                else:
                    datastrs.append(str(data[y][x]))
        return ','.join(datastrs)
        
    
    def getUnitStr(self, ulist, unit):
        if unit == 0:
            minval = min(ulist)
            maxval = max(ulist)
            if (maxval - minval) > 40:
                return -1, -1, None
            years = ['%d'%x for x in range(minval,maxval+1)]
            str = '["'+'","'.join(years)+'"]'
            
        elif unit == 1:
            minval = 1
            maxval = 12
            str =  '["January","February","March","April","May","June","July","August","September","October","November","December"]'
        elif unit == 2:
            minval = 1
            maxval = 31
            str = '["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31"]'
        elif unit == 3:
            minval = 0
            maxval = 6
            str = '["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]'
        else:
            minval = 0
            maxval = 23
            str = '["Midnight", "1am", "2am", "3am", "4am", "5am", "6am", "7am", "8am", "9am", "10am", "11am", "Noo", "1pm", "2pm", "3pm", "4pm", "5pm", "6pm", "7pm", "8pm", "9pm", "10pm", "11pm"]'
        return minval, maxval, str
        
    def close(self):
        self.hide()
        
def replaceInTemplate(template, values):
    path = os.path.join(os.path.dirname(__file__), "templates", template)
    with open(path) as f:
        lines = f.readlines()
    s = "".join(lines)
    for name,value in values.iteritems():
        s = s.replace(name, value)
    return s

LAST_PATH = "LastPath"

def askForFolder(parent, name="HeatmapPath"):
    path = getSetting(LAST_PATH, name)
    folder =  QFileDialog.getExistingDirectory(parent, "Select folder to store chart", path)
    if folder:
        setSetting(LAST_PATH, name, folder)
    return folder


def setSetting(namespace, name, value):
    settings = QSettings()
    settings.setValue(namespace + "/" + name, value)

def getSetting(namespace, name):
    v = QSettings().value(namespace + "/" + name, None)
    if isinstance(v, QPyNullVariant):
        v = None
    return v