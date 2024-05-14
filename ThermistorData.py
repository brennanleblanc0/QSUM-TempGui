from mcculw import ul
from mcculw.enums import ULRange
from mcculw.ul import ULError
from PyQt6 import QtWidgets
import time, datetime
import math
import os

class ThermistorData():
    @staticmethod
    def readDaq(window, interval) -> None:
        t_0 = datetime.datetime.now(datetime.UTC).timestamp()
        fileName = f"{os.getcwd()}/logs/QSUM_TempLog_{datetime.datetime.now(datetime.UTC).strftime("%m.%Y")}.txt"
        if os.path.exists(fileName):
            f = open(fileName, "a")
        else:
            f = open(fileName, "w")
            f.write("QSUM Temperature and Humidity Monitor Log\n")
            f.write("Device:TSP01B\n")
            f.write("S/N:M00995273\n")
            f.write(f"Measurement Interval:{interval}\n")
            f.write(f"Begin Data Table\n")
            f.write("Time [s]\tDate\tTime\tTemperature[°C]\tHumidity[%]\tTH1[°C]\tTH2[°C]\n")
            f.flush()
        board_num = 0
        channel = 0
        ai_range = ULRange.BIP10VOLTS
        while True:
            try:
                # Get a value from the device
                value = ul.a_in(board_num, channel, ai_range)
                # Convert the raw value to engineering units
                eng_units_value = ul.to_eng_units(board_num, ai_range, value)

                temp = 3988/math.log((10000*((5/eng_units_value)-1))/(10000*math.exp(-3988/298.15))) - 273.15
                window.curTempNumber.display("{:.2f}".format(temp))
                if (datetime.datetime.now(datetime.UTC).timestamp() - t_0) >= interval:
                    t_0 = datetime.datetime.now(datetime.UTC).timestamp()
                    f.write(f"New\t{datetime.datetime.fromtimestamp(t_0).strftime("%b %d %Y\t%H:%M:%S")}\t{temp:.2f}\t{0.0:.2f}\t--\t--\n")
                    f.flush()
            except ULError as e:
                # Display the error
                print("A UL error occurred. Code: " + str(e.errorcode)
                      + " Message: " + e.message)
            except (ValueError, ZeroDivisionError) as e:
                print("ValueError occurred. Is the Thermistor properly seated? " + e.__str__())
            time.sleep(0.5)