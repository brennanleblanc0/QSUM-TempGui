from PyQt6.QtWidgets import QWidget
from datetime import datetime
import threading
import os
import scipy.signal as signal

class OldDataParser():
    @staticmethod
    def parseData(fileName:str, resolutionIndex:int) -> list:
        resFactor = 1 if resolutionIndex == 0 else 2 if resolutionIndex == 1 else 10
        try:
            f = open(fileName, encoding="iso-8859-1")
        except:
            print("ERROR: Does that file exist?")
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
        def __oldDataLoopBody(arr, i):
            for j in range(i, len(arr), os.cpu_count()):
                x = arr[j]
                tokens = x.split("\t")
                dateString = tokens[1] + " " + tokens[2]
                convDateTime = datetime.strptime(dateString, "%b %d %Y %H:%M:%S")
                output[0][j] = convDateTime.timestamp()
                output[1][j] = float(tokens[3])
                output[2][j] = float(tokens[4])
                output[3][j] = tokens[5]
                output[4][j] = tokens[6][0:len(tokens[6])-1]
        for k in range(0,os.cpu_count()):
            newThread = threading.Thread(None, __oldDataLoopBody, None, [arr, k])
            threads.append(newThread)
            newThread.start()
        for e in threads:
            e.join()
        f.close()
        return output
    
    @staticmethod
    def parseDateRange(startDate:float, endDate:float, resolutionIndex:int, logsDir:str) -> list:
        resFactor = 1 if resolutionIndex == 0 else 2 if resolutionIndex == 1 else 10
        startMonth = int(datetime.fromtimestamp(startDate).strftime("%m"))
        endMonth = int(datetime.fromtimestamp(endDate).strftime("%m"))
        startYear = int(datetime.fromtimestamp(startDate).strftime("%Y"))
        endYear = int(datetime.fromtimestamp(endDate).strftime("%Y"))
        threads = []
        i = 0
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
                                raise Exception
                            eCount += 1
                    f.close()
                    j += 1
            except Exception as err:
                print(err)
                startMonth += 1
                if startMonth > 12:
                    startMonth = 1
                    startYear += 1
        output = [[None]*len(arr), [None]*len(arr), [None]*len(arr), [None]*len(arr), [None]*len(arr)]
        def __oldDataLoopBody(arr, i):
            for j in range(i, len(arr), os.cpu_count()):
                x = arr[j]
                tokens = x.split("\t")
                dateString = tokens[1] + " " + tokens[2]
                convDateTime = datetime.strptime(dateString, "%b %d %Y %H:%M:%S")
                output[0][j] = convDateTime.timestamp()
                output[1][j] = float(tokens[3])
                output[2][j] = float(tokens[4])
                output[3][j] = tokens[5]
                output[4][j] = tokens[6][0:len(tokens[6])-1]
        for j in range(0,os.cpu_count()):
            newThread = threading.Thread(None, __oldDataLoopBody, None, [arr, j])
            threads.append(newThread)
            newThread.start()
        for e in threads:
            e.join()
        return output
    
    @staticmethod
    def psdAndWelch(window, data, disPoints, splitFactor):
        bestRange = -1
        for i in range(0, len(disPoints)):
            # if i == 0:
            #     f_p, P_p = signal.periodogram(data[1][0:disPoints[i]+1], window='hann', scaling='density')
            #     f_w, P_w = signal.welch(data[1][0:disPoints[i]+1], scaling='density')
            # elif i == len(disPoints) - 1:
            #     f_p2, P_p2 = signal.periodogram(data[1][disPoints[i-1]+1:disPoints[i]+1], window='hann', scaling='density')
            #     f_w2, P_w2 = signal.welch(data[1][disPoints[i-1]+1:disPoints[i]+1], scaling='density')
            #     window.analysisMpl.axes.semilogy(f_p2/1e3, P_p2)
            #     window.analysisMpl.axes.semilogy(f_w2/1e3, P_w2)
            #     f_p, P_p = signal.periodogram(data[1][disPoints[i]+1:], window='hann', scaling='density')
            #     f_w, P_w = signal.welch(data[1][disPoints[i]+1:], scaling='density')
            # else:
            #     f_p, P_p = signal.periodogram(data[1][disPoints[i-1]+1:disPoints[i]+1], window='hann', scaling='density')
            #     f_w, P_w = signal.welch(data[1][disPoints[i-1]+1:disPoints[i]+1], scaling='density')
            # window.analysisMpl.axes.semilogy(f_p/1e3, P_p)
            # window.analysisMpl.axes.semilogy(f_w/1e3, P_w)
            if bestRange == -1 and i != 0:
                if disPoints[0] < disPoints[i] - disPoints[i-1]:
                    bestRange = i
            elif i != 0:
                if disPoints[bestRange] - disPoints[bestRange-1] < disPoints[i] - disPoints[i-1]:
                    bestRange = i
        if bestRange == -1:
            f_p, P_p = signal.periodogram(data[1][0:disPoints[0]+1], fs=1/10, window='hann', scaling='density')
            
        else:
            f_p, P_p = signal.periodogram(data[1][disPoints[bestRange-1]+1:disPoints[bestRange]+1:2], fs=1/10, window='hann', scaling='density')
            f_w, P_w = OldDataParser.__pseudo_welch(data, splitFactor)

        window.analysisMpl.axes.loglog(f_p*3600, P_p)
        window.analysisMpl.axes.loglog(f_w*3600, P_w)
        window.analysisMpl.axes.grid(True)
        window.analysisMpl.draw()
        print(disPoints)
        print(bestRange)
    @staticmethod
    def __pseudo_welch(data, splitFactor):
        pass
