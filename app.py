from PyQt6 import QtCore, QtWidgets, uic
import matplotlib.axes
import matplotlib.figure
import matplotlib.pyplot
import matplotlib.dates as mdates
from pyqtgraph import PlotWidget
from CustomGuiUtils import OldDataParser
from DeviceReader import DeviceReader
from datetime import datetime, timezone
import threading
import pyqtgraph as pg
import sys
import os
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

# TODO:
# - Switch from threading to multiprocessing: We gain better speedup across multiple cores at the cost of shared memory
# (some instances should still use threading but data grabbing, for example, benefits from multiprocessing)

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=100, height=100, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        uic.loadUi("mainwindow.ui", self)
        # ======= Widget Setup =======
        # Analysis Tab
        self.analysisMpl = MplCanvas(self)
        toolbar = NavigationToolbar2QT(self.analysisMpl, self)
        self.analysisWidget.addWidget(toolbar)
        self.analysisWidget.addWidget(self.analysisMpl)
        self.analysisButton.pressed.connect(self.genButtonPressed)
        self.intervalSpin.setValue(10)
        # Hold on to data
        self.curData = None
        self.curDisPoints = None
        # Pre-populate file selection
        curDate = datetime.now(timezone.utc).strftime("%m.%Y")
        self.browseSaveLine.setText(f"{os.getcwd()}/logs/QSUM_TempLog_{curDate}.txt")
        self.browseLoadLine.setText(f"{os.getcwd()}/logs/QSUM_TempLog_{curDate}.txt")
        # # Graph tab
        # self.tempWidget.setAxisItems({'bottom':pg.DateAxisItem(orientation='bottom')})
        # self.humidWidget.setAxisItems({'bottom':pg.DateAxisItem(orientation='bottom')})
        # All Options widgets setup
        self.saveFileButton.pressed.connect(self.saveFile)
        self.loadFileButton.pressed.connect(self.loadFile)
        self.browseSave.pressed.connect(self.browseSavePressed)
        self.browseLoad.pressed.connect(self.browseLoadPressed)
        self.loadFileWidget.setEnabled(False)
        self.loadDateWidget.setEnabled(False)
        self.loadFileRadio.toggled.connect(self.loadFileHasChanged)
        self.loadDateRadio.toggled.connect(self.loadDateHasChanged)
        self.loadFileRadio.toggle()
        self.stopButton.pressed.connect(self.stopButtonPressed)
        # Start live data without logging
        self.dataThread = DeviceReader(self, 10, self.averageCheck.isChecked(), self.browseSaveLine.text(), False)
        self.dataThread.start()
    def displayData(self):
        # ======= Reset Graphs =======
        self.tempWidget.axes.clear()
        self.humidWidget.axes.clear()
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)
        # ======= Data Collection =======
        resolution = self.resolutionCombo.currentIndex()
        if self.loadDateRadio.isChecked():
            data = OldDataParser.parseDateRange(datetime.strptime(self.startDate.date().toPyDate().strftime("%Y-%m-%d 00:00:00"), "%Y-%m-%d %H:%M:%S").timestamp(), datetime.strptime(self.endDate.date().toPyDate().strftime("%Y-%m-%d 23:59:59"), "%Y-%m-%d %H:%M:%S").timestamp(), resolution, f"{os.getcwd()}/logs")
        else:
            data = OldDataParser.parseData(self.browseLoadLine.text(), resolution)
        self.curData = data
        # ======= Find Discontinuities =======
        disPoints = []
        threads = []
        # Helper method for threading
        def __discontinuity(i):
            for i in range(i, len(data[0]), os.cpu_count()):
                if i == len(data[0]) - 1:
                    disPoints.append(i)
                elif data[0][i+1] - data[0][i] > 11 * (1 if resolution == 0 else 2 if resolution == 1 else 10):
                    disPoints.append(i)
        # Create as many threads as "cpus" detected by the system
        for j in range(0,os.cpu_count()):
            newThread = threading.Thread(None, __discontinuity, None, [j])
            threads.append(newThread)
            newThread.start()
        for e in threads:
            e.join()
        disPoints.sort()
        self.curDisPoints = disPoints
        # ======== Table Entry ========
        self.tableWidget.setHorizontalHeaderLabels(["Time [yyyy-mm-dd hh:mm:ss]", "Temperature [°C]", "rel. Humidity [%]", "TH1 [°C]", "TH2 [°C]"])
        # Helper method for threading
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
        # Create as many threads as "cpus" detected by the system
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
                self.axes.tempWidget.plot(date[0:disPoints[i]+1], temp[0:disPoints[i]+1], color="black")
                self.axes.humidWidget.plot(date[0:disPoints[i]+1], humid[0:disPoints[i]+1], color="black")
            elif i == len(disPoints) - 1:
                self.axes.tempWidget.plot(date[disPoints[i-1]+1:disPoints[i]+1], temp[disPoints[i-1]+1:disPoints[i]+1], color="black")
                self.axes.humidWidget.plot(date[disPoints[i-1]+1:disPoints[i]+1], humid[disPoints[i-1]+1:disPoints[i]+1], color="black")
                self.axes.tempWidget.plot(date[disPoints[i]+1:], temp[disPoints[i]+1:], color="black")
                self.axes.humidWidget.plot(date[disPoints[i]+1:], humid[disPoints[i]+1:], color="black")
            else:
                self.axes.tempWidget.plot(date[disPoints[i-1]+1:disPoints[i]+1], temp[disPoints[i-1]+1:disPoints[i]+1], color="black")
                self.axes.humidWidget.plot(date[disPoints[i-1]+1:disPoints[i]+1], humid[disPoints[i-1]+1:disPoints[i]+1], color="black")
    def loadFileHasChanged(self, s):
        self.loadFileWidget.setEnabled(s)
    def loadDateHasChanged(self, s):
        self.loadDateWidget.setEnabled(s)
    def saveFile(self):
        if not self.dataThread == None:
            self.dataThread.raise_exception()
            self.dataThread.join()
        self.dataThread = DeviceReader(self, self.intervalSpin.value(), self.averageCheck.isChecked(), self.browseSaveLine.text(), True)
        self.dataThread.start()
        self.statusLabel.setText("Logging in progress...")
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
        if not self.curData == None:
            self.analysisMpl.axes.clear()
            newThread = threading.Thread(None, OldDataParser.psdAndWelch, None, [self, self.curData, self.curDisPoints, int(self.welchCombo.currentText()), self.intervalSpin.value()])
            newThread.start()
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Analysis Warning",
                "No data has been loaded. Please load data before using the Analysis tab.",
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
        self.dataThread = DeviceReader(self, self.intervalSpin.value(), self.averageCheck.isChecked(), self.browseSaveLine.text(), False)
        self.dataThread.start()
        self.statusLabel.setText("Logging stopped.")

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec()

if __name__ == '__main__':
    main()
