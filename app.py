from PyQt6 import QtCore, QtWidgets, uic
from pyqtgraph import PlotWidget
from CustomGuiUtils import OldDataParser
from DeviceReader import DeviceReader
from datetime import datetime
import threading
import pyqtgraph as pg
import sys
import os

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        uic.loadUi("mainwindow.ui", self)
        self.loadBox.setEnabled(False)
        self.saveBox.setEnabled(False)
        self.loadRadio.toggled.connect(self.loadHasChanged)
        self.saveRadio.toggled.connect(self.saveHasChanged)
        self.saveRadio.toggle()
        self.browseSaveLine.setText(f"{os.getcwd()}/logs/QSUM_TempLog_{datetime.utcnow().strftime("%m.%Y")}.txt")
        self.browseLoadLine.setText(f"{os.getcwd()}/logs/QSUM_TempLog_{datetime.utcnow().strftime("%m.%Y")}.txt")
        self.displayData()
        self.tempWidget.setAxisItems({'bottom':pg.DateAxisItem(orientation='bottom')})
        self.humidWidget.setAxisItems({'bottom':pg.DateAxisItem(orientation='bottom')})
        self.saveFileButton.pressed.connect(self.saveFile)
        self.loadFileButton.pressed.connect(self.loadFile)
        self.browseSave.pressed.connect(self.browseSavePressed)
        self.browseLoad.pressed.connect(self.browseLoadPressed)
        self.loadFileWidget.setEnabled(False)
        self.loadDateWidget.setEnabled(False) 
        self.loadFileRadio.toggled.connect(self.loadFileHasChanged)
        self.loadDateRadio.toggled.connect(self.loadDateHasChanged)
        self.loadFileRadio.toggle()
    def displayData(self):
        self.tempWidget.clear()
        self.humidWidget.clear()
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)
        resolution = self.resolutionCombo.currentIndex() if self.loadRadio.isChecked() else 0
        if self.loadRadio.isChecked() and self.loadDateRadio.isChecked():
            data = OldDataParser.parseDateRange(datetime.strptime(self.startDate.date().toPyDate().strftime("%Y-%m-%d 00:00:00"), "%Y-%m-%d %H:%M:%S").timestamp(), datetime.strptime(self.endDate.date().toPyDate().strftime("%Y-%m-%d 23:59:59"), "%Y-%m-%d %H:%M:%S").timestamp(), resolution, f"{os.getcwd()}/logs")
        else:
            data = OldDataParser.parseData(self.browseSaveLine.text() if self.saveRadio.isChecked() else self.browseLoadLine.text(), resolution)
        plotThread = threading.Thread(None, self.plot, None, [data[0], data[1], data[2], resolution])
        plotThread.start()
        self.tableWidget.setHorizontalHeaderLabels(["Time [yyyy-mm-dd hh:mm:ss]", "Temperature [°C]", "rel. Humidity [%]", "TH1 [°C]", "TH2 [°C]"])
        def __tableThreaded(i):
            dateItem = QtWidgets.QTableWidgetItem(datetime.fromtimestamp(data[0][i]).strftime("%Y-%m-%d %H:%M:%S"))
            dateItem.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            self.tableWidget.setItem(i,0,dateItem)
            for j in range(1,5):
                newItem = QtWidgets.QTableWidgetItem(str(data[j][i]))
                newItem.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
                self.tableWidget.setItem(i,j,newItem)
        for i in range(0,len(data[0])):
            self.tableWidget.insertRow(i)
            newThread = threading.Thread(None, __tableThreaded, None, [i])
            newThread.start()
    def plot(self, date, temp, humid, resolution):
        if len(date) == 0:
            return
        lastPlt = 0
        for i in range(0, len(date)):
            if i == len(date) - 1:
                self.tempWidget.plot(date[lastPlt:len(date)], temp[lastPlt:len(date)])
                self.humidWidget.plot(date[lastPlt:len(date)], humid[lastPlt:len(date)])
            elif date[i+1] - date[i] > 11 * (1 if resolution == 0 else 2 if resolution == 1 else 10):
                self.tempWidget.plot(date[lastPlt:i+1], temp[lastPlt:i+1])
                self.humidWidget.plot(date[lastPlt:i+1], humid[lastPlt:i+1])
                lastPlt = i + 1
    def loadHasChanged(self, s):
        self.loadBox.setEnabled(s)
    def saveHasChanged(self, s):
        self.saveBox.setEnabled(s)
    def loadFileHasChanged(self, s):
        self.loadFileWidget.setEnabled(s)
    def loadDateHasChanged(self, s):
        self.loadDateWidget.setEnabled(s)
    def saveFile(self):
        newThread = threading.Thread(None, self.displayData, None, [])
        newThread.start()
    def loadFile(self):
        newThread = threading.Thread(None, self.displayData, None, [])
        newThread.start()
    def browseSavePressed(self):
        getFile = QtWidgets.QFileDialog.getOpenFileName(self, "Save As...", "./", "Text files (*.txt)")
        if len(getFile[0]) > 0:
            self.browseSaveLine.setText(getFile[0])
    def browseLoadPressed(self):
        getFile = QtWidgets.QFileDialog.getOpenFileName(self, "Open...", "./", "Text files (*.txt)")
        if len(getFile[0]) > 0:
            self.browseLoadLine.setText(getFile[0])

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec()

if __name__ == '__main__':
    main()