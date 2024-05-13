from PyQt6.QtWidgets import QWidget
from datetime import datetime
import threading

class OldDataParser():
    @staticmethod
    def parseData(fileName:str, resolutionIndex:int) -> list:
        resFactor = 1 if resolutionIndex == 0 else 2 if resolutionIndex == 1 else 10
        try:
            f = open(fileName, encoding="iso-8859-1")
        except:
            f = open(fileName, "w")
            f.close()
            return [[],[],[],[],[]]
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
            for j in range(i, len(arr), 6):
                x = arr[j]
                tokens = x.split("\t")
                dateString = tokens[1] + " " + tokens[2]
                convDateTime = datetime.strptime(dateString, "%b %d %Y %H:%M:%S")
                output[0][j] = convDateTime.timestamp()
                output[1][j] = float(tokens[3])
                output[2][j] = float(tokens[4])
                output[3][j] = tokens[5]
                output[4][j] = tokens[6][0:len(tokens[6])-1]
        for k in range(0,6):
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
                    f = open(f"{logsDir}/QSUM_TempLog_{startMonth if startMonth >= 10 else f"0{startMonth}"}.{startYear}_{j}.txt", encoding="iso-8859-1")
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
            for j in range(i, len(arr), 6):
                x = arr[j]
                tokens = x.split("\t")
                dateString = tokens[1] + " " + tokens[2]
                convDateTime = datetime.strptime(dateString, "%b %d %Y %H:%M:%S")
                output[0][j] = convDateTime.timestamp()
                output[1][j] = float(tokens[3])
                output[2][j] = float(tokens[4])
                output[3][j] = tokens[5]
                output[4][j] = tokens[6][0:len(tokens[6])-1]
        for j in range(0,6):
            newThread = threading.Thread(None, __oldDataLoopBody, None, [arr, j])
            threads.append(newThread)
            newThread.start()
        for e in threads:
            e.join()
        return output
    