from PyQt6.QtWidgets import QWidget, QMainWindow
from datetime import datetime
import threading
import os
import scipy.signal as signal
import numpy as np

class OldDataParser():
    @staticmethod
    def parseData(window:QMainWindow, fileName:str, resolutionIndex:int) -> list:
        resFactor = 1 if resolutionIndex == 0 else 2 if resolutionIndex == 1 else 10
        try:
            f = open(fileName, encoding="iso-8859-1")
        except:
            window.statusBar.showMessage("ERROR: Does that file exist?", 10)
        threads = []
        i = 0
        arr = []
        for x in f:
            if i < 6:
                pass
            else:
                if (i-6) % resFactor == 0:
                    arr.append(x)
            i += 1
        output = [[None]*len(arr), [None]*len(arr), [None]*len(arr), [None]*len(arr), [None]*len(arr)]
        for k in range(0,os.cpu_count()):
            newThread = threading.Thread(None, OldDataParser.__oldDataLoopBody, None, [arr, k, output])
            threads.append(newThread)
            newThread.start()
        for e in threads:
            e.join()
        f.close()
        output.append("File 1")
        return [output]
    
    @staticmethod
    def parseDateRange(startDate:float, endDate:float, resolutionIndex:int, logsDir:str) -> list:
        resFactor = 1 if resolutionIndex == 0 else 2 if resolutionIndex == 1 else 10
        startMonth = int(datetime.fromtimestamp(startDate).strftime("%m"))
        endMonth = int(datetime.fromtimestamp(endDate).strftime("%m"))
        startYear = int(datetime.fromtimestamp(startDate).strftime("%Y"))
        endYear = int(datetime.fromtimestamp(endDate).strftime("%Y"))
        threads = []
        allArr = []
        arr = []
        eCount = 0
        while startMonth <= endMonth and startYear <= endYear:
            try:
                j = 1
                k = 0
                while True:
                    k = 0
                    ternState = startMonth if startMonth >= 10 else f"0{startMonth}"
                    f = open(f"{logsDir}/QSUM_TempLog_{ternState}.{startYear}_{j}.txt", encoding="iso-8859-1")
                    for x in f:
                        if k < 6:
                            k += 1
                        else:
                            tokens = x.split("\t")
                            convDateTime = datetime.strptime(f"{tokens[1]} {tokens[2]}", "%b %d %Y %H:%M:%S")
                            if convDateTime.timestamp() >= startDate and convDateTime.timestamp() <= endDate:
                                if eCount % resFactor == 0:
                                    arr.append(x)
                                eCount += 1
                            elif convDateTime.timestamp() > endDate:
                                f.close()
                                allArr.append(arr)
                                arr = []
                                raise Exception
                            eCount += 1
                    f.close()
                    j += 1
                    allArr.append(arr)
                    arr = []
            except Exception as err:
                startMonth += 1
                if startMonth > 12:
                    startMonth = 1
                    startYear += 1
        allOut = []
        i = 1
        for a in allArr:
            output = [[None]*len(a), [None]*len(a), [None]*len(a), [None]*len(a), [None]*len(a)]
            for j in range(0,os.cpu_count()):
                newThread = threading.Thread(None, OldDataParser.__oldDataLoopBody, None, [a, j, output])
                threads.append(newThread)
                newThread.start()
            for e in threads:
                e.join()
            output.append(f"File {i}")
            i+=1
            allOut.append(output)
            threads = []
        return allOut
    
    @staticmethod
    def __oldDataLoopBody(arr, i, outArr):
        for j in range(i, len(arr), os.cpu_count()):
            x = arr[j]
            tokens = x.split("\t")
            dateString = tokens[1] + " " + tokens[2]
            convDateTime = datetime.strptime(dateString, "%b %d %Y %H:%M:%S")
            outArr[0][j] = convDateTime.timestamp()
            outArr[1][j] = float(tokens[3])
            outArr[2][j] = float(tokens[4])
            outArr[3][j] = tokens[5]
            outArr[4][j] = tokens[6][0:len(tokens[6])-1]
    
    @staticmethod
    def psdAndWelch(window:QMainWindow, data:list, splitFactor:int, interval:int, axis:int) -> None:
        comboList = []
        for a in data:
            if len(a[1]) > len(comboList):
                comboList = a[1]

        f_p, P_p = signal.periodogram(comboList, fs=1/interval, window='hann', scaling='density')
        mirrorList = comboList
        mirrorList.reverse()
        distList = mirrorList + comboList + mirrorList
        # f_w, P_w = OldDataParser.__pseudo_welch(comboList, splitFactor, interval)
        f_w, P_w = signal.welch(distList, fs=1/interval, scaling='density', nperseg=len(distList)/splitFactor)

        match axis:
            case 0:
                window.analysisMpl.axes.plot(f_p*3600, np.sqrt(P_p), label="PSD")
                window.analysisMpl.axes.plot(f_w*3600, np.sqrt(P_w), label="Welch")
            case 1:
                window.analysisMpl.axes.semilogx(f_p*3600, np.sqrt(P_p), label="PSD")
                window.analysisMpl.axes.semilogx(f_w*3600, np.sqrt(P_w), label="Welch")
            case 2:
                window.analysisMpl.axes.semilogy(f_p*3600, np.sqrt(P_p), label="PSD")
                window.analysisMpl.axes.semilogy(f_w*3600, np.sqrt(P_w), label="Welch")
            case 3:
                window.analysisMpl.axes.loglog(f_p*3600, np.sqrt(P_p), label="PSD")
                window.analysisMpl.axes.loglog(f_w*3600, np.sqrt(P_w), label="Welch")
        window.analysisMpl.axes.set_xlabel("1/3600 Hz")
        window.analysisMpl.axes.set_ylabel("C√h")
        window.analysisMpl.axes.grid(True)
        window.analysisMpl.axes.legend()
        window.analysisMpl.draw()
    @staticmethod
    def __pseudo_welch(data, splitFactor, interval):
        maxData = len(data) - (len(data) % splitFactor)
        bins = [[]]*splitFactor
        for i in range(0, splitFactor):
            bins[i] = data[i:maxData:splitFactor]
        fws = None
        pws_avg = None
        for i in range(0,splitFactor):
            fws, pws = signal.periodogram(bins[i], fs=1/(interval*splitFactor), window='hann', scaling='density')
            if i == 0:
                pws_avg = pws
            else:
                pws_avg += pws
            
        return (fws, pws_avg/splitFactor)
