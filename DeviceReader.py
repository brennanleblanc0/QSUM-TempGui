from ctypes import *
from PyQt6 import QtWidgets
import time

class DeviceReader():
    @staticmethod
    def dataLogging(liveWin):
        try:
            while True:
                liveWin.displayData()
                time.sleep(10)
        except:
            return
    def liveData(liveWin):
        pass