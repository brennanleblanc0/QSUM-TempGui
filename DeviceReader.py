from ctypes import *
from PyQt6 import QtWidgets
import time, datetime
import threading
import os
import math

class DeviceReader(threading.Thread):
    def __init__(self, window, interval, isAveraging, fileName, isLogging):
        threading.Thread.__init__(self, daemon=True)
        self.window = window
        self.interval = interval
        self.isAveraging = isAveraging
        self.fileName = fileName
        self.isLogging = isLogging
    def run(self):
        if self.isLogging:
            self.__openFile()
        curMonth = int(datetime.datetime.now(datetime.timezone.utc).strftime("%m"))
        lib = cdll.LoadLibrary("C:\Program Files\IVI Foundation\VISA\Win64\Bin\TLTSPB_64.dll")

        #Find out if there are devices connected.
        deviceCount = c_ulong()
        lib.TLTSPB_findRsrc(0, byref(deviceCount))

        #If there are devices connected, determine their names.
        if deviceCount.value >= 1:

            deviceName=create_string_buffer(256)
            
            #If there is only one device, it will be opened. Otherwise, ask which one should be connected.
            if deviceCount.value ==1:
                lib.TLTSPB_getRsrcName(0, 0, deviceName)
            else:
                print("Which device?")
                for i in range(deviceCount.value):
                    lib.TLTSPB_getRsrcName(0, i, deviceName)
                    print('#' + str(i+1) + " " + deviceName.value)
                device_num = input(">>>")
                lib.TLTSPB_getRsrcName(0, (device_num-1), deviceName)
            try:
                t_0 = math.floor(datetime.datetime.now(datetime.timezone.utc).timestamp())
                prevData = [[],[]]
                #Initialize the device.
                sessionHandle=c_ulong(0)
                lib.TLTSPB_init(deviceName, 0, 0, byref(sessionHandle))
                while True:
                    if self.isLogging and curMonth < int(datetime.datetime.now(datetime.timezone.utc).strftime("%m")):
                        curDate = datetime.datetime.now(datetime.timezone.utc).strftime("%m.%Y")
                        self.fileName = self.__openFile(f"{os.getcwd()}/logs/QSUM_TempLog_{curDate}.txt")
                        self.window.browseSaveLine.setText(self.fileName)
                        self.__openFile()
                    #Declare variables and constants for measurements
                    #See TLTSP_Defines.h and TLTSPB.h for definitions of constants
                    temperature=c_longdouble(0.0)
                    humidity=c_longdouble(0.0)
                    attribute = c_short(0)
                    ch_intern = c_ushort(11)

                    #Returns the temperature measured by the internal sensor in the TSP01 in °C.
                    lib.TLTSPB_getTemperatureData(sessionHandle, ch_intern, attribute, byref(temperature))

                    #This returns the humidity measured by the internal sensor in the TSP01.
                    lib.TLTSPB_getHumidityData(sessionHandle, attribute, byref(humidity))

                    temp = temperature.value
                    humid = humidity.value
                    self.window.curTempNumber.display("{:.2f}".format(temp))
                    self.window.curHumidNumber.display("{:.2f}".format(humid))
                    if self.isLogging:
                        prevData[0].append(temp)
                        prevData[1].append(humid)
                    if self.isLogging and (datetime.datetime.now(datetime.timezone.utc).timestamp() - t_0) >= self.interval:
                        t_0 = math.floor(datetime.datetime.now(datetime.timezone.utc).timestamp())
                        curTime = datetime.datetime.fromtimestamp(t_0).strftime("%b %d %Y\t%H:%M:%S")
                        if self.isAveraging:
                            avgT = 0
                            avgH = 0
                            for i in range(0, len(prevData[0])):
                                avgT += prevData[0][i]
                                avgH += prevData[1][i]
                            avgT /= len(prevData[0])
                            avgH /= len(prevData[1])
                            stdDevT = 0
                            stdDevH = 0
                            for i in range(0, len(prevData[0])):
                                stdDevT += (prevData[0][i] - avgT)**2
                                stdDevH += (prevData[1][i] - avgH)**2
                            stdDevT = math.sqrt(stdDevT / len(prevData[0]))
                            stdDevH = math.sqrt(stdDevH / len(prevData[1]))
                            self.f.write(f"New\t{curTime}\t{avgT:.2f}\t{avgH:.2f}\t--\t--\t{stdDevT}\t{stdDevH}\n")
                        else:
                            self.f.write(f"New\t{curTime}\t{temp:.2f}\t{humid:.2f}\t--\t--\t--\n")
                        self.f.flush()
                        prevData = [[],[]]
            finally:
                if self.isLogging:
                    self.f.close()
                #Close the connection to the TSP01 Rev. B.
                lib.TLTSPB_close(sessionHandle)
        else:
            print("No connected TSP01 Rev. B devices were detected. Check connections and installed drivers.")
    def __openFile(self):
        if os.path.exists(self.fileName):
            self.f = open(self.fileName, "a")
        else:
            self.f = open(self.fileName, "w")
            self.f.write("QSUM Temperature and Humidity Monitor Log\n")
            self.f.write("Device:TSP01B\n")
            self.f.write("S/N:M00995273\n")
            self.f.write(f"Measurement Interval:{self.interval}\n")
            self.f.write(f"Begin Data Table\n")
            self.f.write("Time [s]\tDate\tTime\tTemperature[°C]\tHumidity[%]\tTH1[°C]\tTH2[°C]\tStd. Dev Temp\t Std. Dev Humid\n")
            self.f.flush()
    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id
    def raise_exception(self):
        thread_id = self.get_id()
        res = pythonapi.PyThreadState_SetAsyncExc(thread_id, py_object(SystemExit))
        if res > 1:
            pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')