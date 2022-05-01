import lib.configFile as configFile
import datetime
from rpi_sleepmeter import awake
import lib.sheetsApi as sheetsApi

config = configFile.getConfig()
buffer = config["buffer"]

def saveAsleep():
    with open(buffer, "r") as f:
        content = f.readlines()
    with open(buffer, "w") as f2:
        lines = ["asleep\n", datetime.datetime.now().strftime("%d.%m.%Y\n"), datetime.datetime.now().strftime("%H:%M:%S\n"), datetime.datetime.now().strftime("%H:%M:%S\n")]
        f2.writelines(content + lines)

def saveAwake():
    with open(buffer, "r") as f:
        content = f.readlines()
    with open(buffer, "w") as f2:
        lines = ["awake\n", datetime.datetime.now().strftime("%H:%M:%S\n")]
        f2.writelines(content + lines)

def saveBufferOnline():
    sheet = sheetsApi.getSheet()
    with open(buffer, "r") as f:
        content = f.readlines()
    while content:
        if content[0].rstrip("\n") == "asleep":
            print("uploading buffered asleep")
            sheet.insert_row([content[1].rstrip("\n"), content[2].rstrip("\n"), content[3].rstrip("\n")], 2, "USER_ENTERED")
            with open(buffer,"w") as f2:
                f2.truncate(0)
                f2.writelines(content[4:])
            with open(buffer, "r") as f3:
                content = f3.readlines()
        if content[0].rstrip("\n") == "awake":
            print("uploading buffered awake")
            awake(content[1], True, sheet, config["alarmClock"]["sleepDelay"])
            with open(buffer,"w") as f4:
                f4.truncate(0)
                f4.writelines(content[2:])