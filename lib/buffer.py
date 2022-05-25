import lib.configFile as configFile
import datetime
from rpi_sleepmeter import awake
import lib.sheetsApi as sheetsApi
import time
import gspread

config = configFile.getConfig()
buffer = config["buffer"]

def saveAsleep():
    with open(buffer, "r") as f:
        content = f.readlines()
    with open(buffer, "w") as f:
        lines = ["asleep\n", datetime.datetime.now().strftime("%d.%m.%Y\n"), datetime.datetime.now().strftime("%H:%M:%S\n"), datetime.datetime.now().strftime("%H:%M:%S\n")]
        f.writelines(content + lines)

def saveAwake():
    with open(buffer, "r") as f:
        content = f.readlines()
    with open(buffer, "w") as f:
        lines = ["awake\n", datetime.datetime.now().strftime("%H:%M:%S\n")]
        f.writelines(content + lines)

def saveBufferOnline():
    sheet = sheetsApi.getSheet()
    with open(buffer, "r") as f:
        content = f.readlines()
    while content:
        try:
            if content[0] == "\n":
                with open(buffer,"w") as f:
                    f.truncate(0)
                    f.writelines(content[1:])
            if content[0].rstrip("\n") == "asleep":
                print("uploading buffered asleep")
                sheet.insert_row([content[1].rstrip("\n"), content[2].rstrip("\n"), content[3].rstrip("\n")], 2, "USER_ENTERED")
                with open(buffer,"w") as f:
                    f.truncate(0)
                    f.writelines(content[4:])
            if content[0].rstrip("\n") == "awake":
                print("uploading buffered awake")
                awake(content[1], True, sheet, config["alarmClock"]["sleepDelay"])
                with open(buffer,"w") as f:
                    f.truncate(0)
                    f.writelines(content[2:])
            with open(buffer, "r") as f:
                content = f.readlines()
        except gspread.exceptions.APIError:
            time.sleep(10)

def isNotEmpty():
    with open(buffer, "r") as f:
        content = f.readlines()
    if content:
        return True
    else:
        return False
