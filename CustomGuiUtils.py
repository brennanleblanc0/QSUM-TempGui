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
        output = [[],[],[],[],[]]
        def __oldDataLoopBody(x, i):
            tokens = x.split("\t")
            dateString = tokens[1] + " " + tokens[2]
            convDateTime = datetime.strptime(dateString, "%b %d %Y %H:%M:%S")
            output[0][i] = convDateTime.timestamp()
            output[1][i] = float(tokens[3])
            output[2][i] = float(tokens[4])
            output[3][i] = tokens[5]
            output[4][i] = tokens[6][0:len(tokens[6])-1]
        threads = []
        i = 0
        eCount = 0
        for x in f:
            if i < 6:
                i += 1
            else:
                if eCount % resFactor == 0:
                    for e in output:
                        e.append(None)
                    newThread = threading.Thread(None, __oldDataLoopBody, None, [x, i-6])
                    threads.append(newThread)
                    newThread.start()
                    i += 1
                eCount += 1
        for e in threads:
            e.join()
        f.close()
        return output
    @staticmethod
    def parseDateRange(startDate:float, endDate:float, resolutionIndex:int) -> list:
        resFactor = 1 if resolutionIndex == 0 else 2 if resolutionIndex == 1 else 10
        startMonth = int(datetime.fromtimestamp(startDate).strftime("%m"))
        endMonth = int(datetime.fromtimestamp(endDate).strftime("%m"))
        startYear = int(datetime.fromtimestamp(startDate).strftime("%Y"))
        endYear = int(datetime.fromtimestamp(endDate).strftime("%Y"))
        output = [[],[],[],[],[]]
        def __oldDataLoopBody(i, tokens):
            dateString = tokens[1] + " " + tokens[2]
            convDateTime = datetime.strptime(dateString, "%b %d %Y %H:%M:%S")
            output[0][i] = convDateTime.timestamp()
            output[1][i] = float(tokens[3])
            output[2][i] = float(tokens[4])
            output[3][i] = tokens[5]
            output[4][i] = tokens[6][0:len(tokens[6])-1]
        threads = []
        i = 0
        eCount = 0
        while startMonth <= endMonth and startYear <= endYear:
            try:
                j = 1
                k = 0
                while True:
                    k = 0
                    f = open(f"QSUM_TempLog_{startMonth if startMonth >= 10 else f"0{startMonth}"}.{startYear}_{j}.txt", encoding="iso-8859-1")
                    for x in f:
                        if k < 6:
                            k += 1
                        else:
                            tokens = x.split("\t")
                            convDateTime = datetime.strptime(f"{tokens[1]} {tokens[2]}", "%b %d %Y %H:%M:%S")
                            if convDateTime.timestamp() >= startDate and convDateTime.timestamp() <= endDate:
                                if eCount % resFactor == 0:
                                    for e in output:
                                        e.append(None)
                                    newThread = threading.Thread(None, __oldDataLoopBody, None, [i, tokens])
                                    threads.append(newThread)
                                    newThread.start()
                                    i += 1
                            elif convDateTime.timestamp() > endDate:
                                for e in threads:
                                    e.join()
                                f.close()
                                return output
                            eCount += 1
                    f.close()
                    j += 1
            except Exception as err:
                print(err)
                startMonth += 1
                if startMonth > 12:
                    startMonth = 1
                    startYear += 1
        for e in threads:
            e.join()
        return output