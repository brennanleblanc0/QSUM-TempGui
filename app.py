from PyQt6 import QtCore, QtWidgets, uic
from pyqtgraph import PlotWidget
from CustomGuiUtils import OldDataParser
from DeviceReader import DeviceReader
from datetime import datetime, timezone
from ThermistorData import ThermistorData
import threading
import pyqtgraph as pg
import sys
import os

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        uic.loadUi("mainwindow.ui", self)
        self.curData = []
        self.curDisPoints = []
        self.loadBox.setEnabled(False)
        self.saveBox.setEnabled(False)
        self.loadRadio.toggled.connect(self.loadHasChanged)
        self.saveRadio.toggled.connect(self.saveHasChanged)
        self.saveRadio.toggle()
        curDate = datetime.now(timezone.utc).strftime("%m.%Y")
        self.browseSaveLine.setText(f"{os.getcwd()}/logs/QSUM_TempLog_{curDate}.txt")
        self.browseLoadLine.setText(f"{os.getcwd()}/logs/QSUM_TempLog_{curDate}.txt")
        #self.displayData()
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
        self.analysisButton.pressed.connect(self.genButtonPressed)
        self.intervalSpin.setValue(10)
        self.dataThread = ThermistorData(self, 10, self.averageCheck.isChecked(), self.browseSaveLine.text())
        self.dataThread.start()
        self.stopButton.pressed.connect(self.stopButtonPressed)
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
        self.curData = data
        disPoints = []
        threads = []
        def __discontinuity(i):
            for i in range(i, len(data[0]), os.cpu_count()):
                if i == len(data[0]) - 1:
                    disPoints.append(i)
                elif data[0][i+1] - data[0][i] > 11 * (1 if resolution == 0 else 2 if resolution == 1 else 10):
                    disPoints.append(i)
        for j in range(0,os.cpu_count()):
            newThread = threading.Thread(None, __discontinuity, None, [j])
            threads.append(newThread)
            newThread.start()
        for e in threads:
            e.join()
        disPoints.sort()
        self.curDisPoints = disPoints
        self.tableWidget.setHorizontalHeaderLabels(["Time [yyyy-mm-dd hh:mm:ss]", "Temperature [°C]", "rel. Humidity [%]", "TH1 [°C]", "TH2 [°C]"])
        def __tableThreaded(i):
            for k in range(i, len(data[0]), os.cpu_count()):
                dateItem = QtWidgets.QTableWidgetItem(datetime.fromtimestamp(data[0][k]).strftime("%Y-%m-%d %H:%M:%S"))
                dateItem.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
                self.tableWidget.setItem(k,0,dateItem)
                for j in range(1,5):
                    newItem = QtWidgets.QTableWidgetItem(str(data[j][i]))
                    newItem.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
                    self.tableWidget.setItem(k,j,newItem)
        self.tableWidget.setRowCount(len(data[0]))
        for i in range(0,os.cpu_count()):
            newThread = threading.Thread(None, __tableThreaded, None, [i])
            newThread.start()
        self.plot(data[0], data[1], data[2])
    def plot(self, date, temp, humid):
        if len(date) == 0:
            return
        disPoints = self.curDisPoints
        for i in range(0,len(disPoints)):
            if i == 0:
                self.tempWidget.plot(date[0:disPoints[i]+1], temp[0:disPoints[i]+1])
                self.humidWidget.plot(date[0:disPoints[i]+1], humid[0:disPoints[i]+1])
            elif i == len(disPoints) - 1:
                self.tempWidget.plot(date[disPoints[i-1]+1:disPoints[i]+1], temp[disPoints[i-1]+1:disPoints[i]+1])
                self.humidWidget.plot(date[disPoints[i-1]+1:disPoints[i]+1], humid[disPoints[i-1]+1:disPoints[i]+1])
                self.tempWidget.plot(date[disPoints[i]+1:], temp[disPoints[i]+1:])
                self.humidWidget.plot(date[disPoints[i]+1:], humid[disPoints[i]+1:])
            else:
                self.tempWidget.plot(date[disPoints[i-1]+1:disPoints[i]+1], temp[disPoints[i-1]+1:disPoints[i]+1])
                self.humidWidget.plot(date[disPoints[i-1]+1:disPoints[i]+1], humid[disPoints[i-1]+1:disPoints[i]+1])
    def loadHasChanged(self, s):
        self.loadBox.setEnabled(s)
    def saveHasChanged(self, s):
        self.saveBox.setEnabled(s)
    def loadFileHasChanged(self, s):
        self.loadFileWidget.setEnabled(s)
    def loadDateHasChanged(self, s):
        self.loadDateWidget.setEnabled(s)
    def saveFile(self):
        if not self.dataThread == None:
            self.dataThread.raise_exception()
            self.dataThread.join()
        self.dataThread = ThermistorData(self, self.intervalSpin.value(), self.averageCheck.isChecked(), self.browseSaveLine.text())
        self.dataThread.start()
    def loadFile(self):
        newThread = threading.Thread(None, self.displayData, None, [])
        newThread.start()
    def browseSavePressed(self):
        getFile = QtWidgets.QFileDialog.getOpenFileName(self, "Save As...", f"{os.getcwd()}/logs", "Text files (*.txt)")
        if len(getFile[0]) > 0:
            self.browseSaveLine.setText(getFile[0])
    def browseLoadPressed(self):
        getFile = QtWidgets.QFileDialog.getOpenFileName(self, "Open...", f"{os.getcwd()}/logs", "Text files (*.txt)")
        if len(getFile[0]) > 0:
            self.browseLoadLine.setText(getFile[0])
    def genButtonPressed(self):
        if not self.loadRadio.isChecked():
            QtWidgets.QMessageBox.warning(
                self,
                "Warning",
                "Analysis is not available in Save mode. Please switch to Load mode.",
                buttons=QtWidgets.QMessageBox.StandardButton.Ok,
                defaultButton=QtWidgets.QMessageBox.StandardButton.Ok
            )
    def stopButtonPressed(self):
        if not self.dataThread == None:
            self.dataThread.raise_exception()
            self.dataThread.join()
            self.dataThread = None
            self.curTempNumber.display("0")
            self.curHumidNumber.display("0")

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec()

if __name__ == '__main__':
    main()
