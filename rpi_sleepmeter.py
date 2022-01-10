from __future__ import division
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import webbrowser
import os
import gpiozero
import urllib3
import random
import serial
import suntime
import pytz
import sys
import yaml

# /etc/xdg/autostart/sleepmeter.desktop

# TODO:
#  - lucid dreaming tools

try:
    with open("/home/pi/sleepmeter/config.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
except IOError:
    with open("/home/pi/sleepmeter/configExample.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)


ytList = config["alarmClock"]["ytList"]

allBuffered = False
skip = False
offlineMode = False
awakeDate = 0

holidaysStart = datetime.datetime.strptime(config["holidays"]["holidaysStart"], "%d.%m.%Y")
holidaysEnd = datetime.datetime.strptime(config["holidays"]["holidaysEnd"], "%d.%m.%Y")

sun = suntime.Sun(config["led"]["lat"], config["led"]["lon"])
utc = pytz.UTC

sleepDelay = config["alarmClock"]["sleepDelay"]

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(r"/home/pi/sleepmeter/data/apikey.json", scope)

print("sleepmeter v5.5 gpiorpi")

ser = serial.Serial(config["led"]["port"], 9600, timeout=1)
ser.flush()
time.sleep(1.5)

ser.write("255000000".encode())
line = ser.readline().decode('utf-8').rstrip()
time.sleep(1.3)
ser.write("000255000".encode())
line = ser.readline().decode('utf-8').rstrip()
time.sleep(1.3)
ser.write("000000255".encode())
line = ser.readline().decode('utf-8').rstrip()
time.sleep(1.3)
ser.write("000000000".encode())
line = ser.readline().decode('utf-8').rstrip()

setColor = "000000000"

try:
    client = gspread.authorize(credentials)
    sheet = client.open(config["sheets"]["sheetName"]).sheet1
except:
    print("Offline mode")
    offlineMode = True

b1 = gpiozero.Button(13)
b2 = gpiozero.Button(6)
b3 = gpiozero.Button(10)
b4 = gpiozero.Button(11)
l1 = gpiozero.LED(26)
l2 = gpiozero.LED(9)
bz1 = gpiozero.Buzzer(5) # quiet
bz2 = gpiozero.Buzzer(19) # loud
bz3 = gpiozero.TonalBuzzer(27)
rl1 = gpiozero.OutputDevice(21, False)

classroomTimes = config["alarmClock"]["times"]["classroom"] # 0=monday
onlineTimes = config["alarmClock"]["times"]["online"]
times1optimized = None
times2 = None
times3 = None
buffer = r"/home/pi/sleepmeter/data/buffer.txt"

if config["alarmClock"]["times"]["current"] == "online":
    times1 = onlineTimes
elif config["alarmClock"]["times"]["current"] == "classroom":
    times1 = classroomTimes
else:
    times1 = []

def optimizeAlarms():
    global times1, times1optimized
    now = datetime.datetime.now()
    if now.hour < 12:
        nextWeekday = now.weekday()
    else:
        nextWeekday = now.weekday() + 1
    if nextWeekday == 7:
        nextWeekday = 0
    
    nextAlarm = None
    for i in range(len(times1)):
        if times1[i][:1] == str(nextWeekday):
            nextAlarm = datetime.datetime.strptime(times1[i], "%U.%H:%M:%S")
            alarmBefore = times1[i]
            break
    if nextAlarm == None:
        print("no alarms to optimize")
        return 0

    timeToAlarm = (nextAlarm - now).seconds/(60*60) - (sleepDelay/60) # to decimal hours
    perfectDelta = timeToAlarm % 1.5 # perfect sleep = divisible by 1.5h

    if perfectDelta < config["alarmClock"]["maxOptimization"]:
        times1optimized = str(nextWeekday) + (now + datetime.timedelta(hours=timeToAlarm-perfectDelta)).strftime(".%H:%M:%S")
        print("optimized time", alarmBefore, "to", times1optimized)
    else:
        print("alarms did not get optimized")

    print("delta (minutes):", perfectDelta*60)

def checkColor():
    global setColor
    with open(config["led"]["file"], "r+") as f:
        try:
            val = f.read().strip("\n")[-9:]
        except:
            return None
    if val != setColor:
        if val == "000000000":
            ledColor("none")
            rl1.off()
        else:
            ledColor(val)
            rl1.on()

def whiteTone():
    if sun.get_local_sunrise_time() < utc.localize(datetime.datetime.now()) < sun.get_local_sunset_time():
        return "255255255" # white white
    else:
        return "lowblue" # warm white

def ledColor(color):
    global setColor
    if color == "highblue":
        color = config["led"]["colors"]["highblue"]
    if color == "lowblue":
        color = config["led"]["colors"]["lowblue"]
    if color == "none":
        color = "000000000"
    
    ser.write(color.encode())
    setColor = color
    with open(config["led"]["file"], "w") as f:
        f.write(color)

def ytAlarmClock():
    global ytList
    rl1.on()
    ledColor("highblue")
    webbrowser.get("chromium-browser").open_new_tab("http://www.hasthelargehadroncolliderdestroyedtheworldyet.com/")
    time.sleep(2)
    webbrowser.get("chromium-browser").open_new_tab(ytList[random.randint(0, len(ytList) - 1)])
    koniec = datetime.datetime.now() + datetime.timedelta(minutes=3)
    while 1:
        if datetime.datetime.now() >= koniec:
            os.system("pkill -f chromium")
            beep(0.1, 2, bz2)
            while datetime.datetime.now() <= koniec:
                if b1.is_active:
                    break
                if b2.is_active:
                    bz2.off()
                    return 0
            if not b1.is_active:
                ledColor("255000000")
                bz2.on()
                b1.wait_for_press()
                ledColor("lowblue")
                bz2.off()
                time.sleep(0.5)
            b1.wait_for_inactive()
            print("alarm turned off")
            time.sleep(1)
            rl1.off()
            ledColor("none")
            break
        elif b1.is_active == 1:
            print("alarm turned off")
            time.sleep(1)
            rl1.off()
            ledColor("none")
            os.system("pkill -f chromium")
            break
            
def beep(timeVal, repeats, bz):
    for i in range(repeats):
        bz.on()
        time.sleep(timeVal)
        bz.off()
        if i+1 != repeats:
            time.sleep(timeVal)

def doSkip():
    beep(0.05, 2, bz2)
    global skip
    skip = not skip
    if skip:
        print("next alarm will be skipped")
    else:
        print("skip cancelled")
    time.sleep(0.2)
    b1.wait_for_inactive()
    b2.wait_for_inactive()

def isItTime():
    global times1, times2, times3
    now = datetime.datetime.now().strftime("%U.%H:%M:%S")

    if now in times1: # planned
        return 1
    elif now == times1optimized: # planowane.optimized
        return 1.5
    elif now == times2: # 6hour
        return 2
    elif now == times3: # 10sec
        return 3
    else:
        return 0
            
def saveAsleep():
    global allBuffered
    with open(buffer, "r") as f:
        content = f.readlines()
    with open(buffer, "w") as f2:
        lines = ["asleep\n", datetime.datetime.now().strftime("%d.%m.%Y\n"), datetime.datetime.now().strftime("%H:%M:%S\n"), datetime.datetime.now().strftime("%H:%M:%S\n")]
        f2.writelines(content + lines)
    
    time.sleep(0.5)
    l1.off()
    time.sleep(0.5)
    l1.on()
    time.sleep(0.5)
    
    allBuffered = False

def saveAwake():
    global allBuffered
    with open(buffer, "r") as f:
        content = f.readlines()
    with open(buffer, "w") as f2:
        lines = ["awake\n", datetime.datetime.now().strftime("%H:%M:%S\n")]
        f2.writelines(content + lines)
    
    time.sleep(0.5)
    l1.off()
    time.sleep(0.5)
    l1.on()
    time.sleep(0.5)

    allBuffered = False

def saveBufferOnline():
    time.sleep(0.2)
    l1.off()
    time.sleep(0.2)
    l1.on()
    time.sleep(0.2)
    with open(buffer, "r") as f:
        content = f.readlines()
    if content:
        if content[0].rstrip("\n") == "asleep":
            sheet.insert_row([content[1].rstrip("\n"), content[2].rstrip("\n"), content[3].rstrip("\n")], 2, "USER_ENTERED")
            with open(buffer,"w") as f2:
                f2.truncate(0)
                f2.writelines(content[4:])
            with open(buffer, "r") as f3:
                content = f3.readlines()
        if content[0].rstrip("\n") == "awake":
            awake(content[1], True)    
            with open(buffer,"w") as f4:
                f4.truncate(0)
                f4.writelines(content[2:])
    else:
        global allBuffered
        allBuffered = True

def connectionTest():
    global offlineMode, sheet, client
    if offlineMode:
        try:
            client = gspread.authorize(credentials)
            sheet = client.open("Sen").sheet1
            offlineMode = False
            print("connection attempt successful")
        except:
            print("connection attempt unsuccessful")
            return False
    try:
        url = "https://www.google.com/"
        conn = urllib3.connection_from_url(url)
        conn.request("GET", "/")
        return True
    except:
        return False

def asleep():
        timeVal = datetime.datetime.now().strftime("%H:%M:%S")
        date = datetime.datetime.now().strftime("%d.%m.%Y")

        value = [date, timeVal, timeVal]
        sheet.insert_row(value, 2, "USER_ENTERED")
        print(sheet.row_values(2))
        time.sleep(0.5)
        b1.wait_for_inactive()

def awake(timeVal, fromBuffer):
    global awakeDate, sleepDelay

    if not fromBuffer and len(sys.argv) < 2: # any argument turns this off
        bz2.on()
        n = None
        while n != str(((datetime.datetime.now().timetuple().tm_yday + 1) ** 20))[:6]:
            n = str(input("todays number: "))
        bz2.off()

    sheet.update_cell(2, 4, timeVal)
    sheet.update_cell(2, 5, "=IF(D2-C2>=0; D2-C2; D2-C2+1)")
    sheet.update_cell(2, 6, "=IF(B2<=0,5;B2+1;B2)")
    sheet.update_cell(2, 7, "=IF(C2<=0,5;C2+1;C2)")
    sheet.update_cell(2, 8, "=IF(B2>0,5;A2;A2-1)")
        
    cell = sheet.cell(2, 2).value
    value = (datetime.datetime.strptime(cell, "%H:%M:%S") + datetime.timedelta(minutes=sleepDelay)).strftime("%H:%M:%S")
    
    sheet.update_cell(2, 3, value)
    awakeDate = datetime.datetime.now().strftime("%d.%m")

if connectionTest():
    while allBuffered == False:
        saveBufferOnline()

rl1.off()
l1.on()
beep(0.1, 3, bz1)

while True:
    if b1.is_pressed:
        rl1.on()
        time.sleep(0.5)
        if b2.is_pressed:
            doSkip()
            time.sleep(3)
            rl1.off()
            continue
        if b1.is_pressed:
            print("6h sleep")
            times2 = (datetime.datetime.now() + datetime.timedelta(hours=6, minutes=sleepDelay)).strftime("%H:%M:%S")
            print(times2)
            beep(0.1, 1, bz1)
        else:
            times2 = None
        l1.off()
        ledColor("lowblue")
        print("asleep")
        beep(0.1, 1, bz1)
        if connectionTest():
            while allBuffered == False:
                saveBufferOnline()
            asleep()
            beep(0.2, 2, bz1)
        else:
            print("saving offline")
            ledColor("lowblue")
            saveAsleep()
            beep(0.5, 1, bz1)
        time.sleep(0.5)
        b1.wait_for_inactive()
        optimizeAlarms()
        print("===============================")
        time.sleep(5)
        rl1.off()
        l1.on()
        ledColor("none")
    elif b2.is_pressed:
        rl1.on()
        time.sleep(0.5)
        if b1.is_pressed:
            doSkip()
            time.sleep(3)
            rl1.off()
            continue
        l1.off()
        ledColor("highblue")
        print("awake")
        beep(0.1, 1, bz2)
        if connectionTest():
            while allBuffered == False:
                saveBufferOnline()
            awake(datetime.datetime.now().strftime("%H:%M:%S"), False)
            beep(0.2, 2, bz1)
            webbrowser.get("chromium-browser").open_new_tab(config["alarmClock"]["weatherURL"])
            time.sleep(60)
            os.system("pkill -f chromium")
        else:
            print("saving offline")
            ledColor("255000000")
            saveAwake()
            beep(0.5, 1, bz1)    
        times2 = None
        times3 = None
        print("===============================")
        time.sleep(3)
        rl1.off()
        l1.on()
        ledColor("none")
    elif b3.is_pressed:
        rl1.toggle()
        if rl1.is_active:
            ledColor(whiteTone())
        else:
            ledColor("none")
        time.sleep(0.5)
        if b3.is_pressed:
            if not rl1.is_active:
                time.sleep(0.5)
                ledColor(whiteTone())
                rl1.on()
            selcolor = input("Enter color value (255255255): ")
            ledColor(str(selcolor))
    else:
        iit = isItTime()
        
        if iit > 0 :
            if skip == True:
                if iit != 1.5: # zoptymalizowane powinny byc pomijane razem ze standardowymi
                    skip = False
                print("skipped #" + iit)
                time.sleep(1)
            elif holidaysStart <= datetime.datetime.now() <= holidaysEnd and iit != 2: # 6godzinne powinny dzialac w wakacje, 10s nie wystapia
                print("holidays, skipping alarm")
                time.sleep(1)
            elif datetime.datetime.now().strftime("%d.%m") == awakeDate:
                times2 = None
                times3 = None
            else:
                if iit == 1:
                    ytAlarmClock()
                elif iit == 1.5:
                    print("optimized alarm")
                    ytAlarmClock()
                elif iit == 2:
                    print("6h alarm")
                    ytAlarmClock()
                elif iit == 3:
                    ledColor("255000000")
                    rl1.on()
                    bz2.on()
                    time.sleep(1)
                    b1.wait_for_press()
                    bz2.off()
                    time.sleep(0.5)
                    b1.wait_for_inactive()
                    time.sleep(1)
                    rl1.off()
                    ledColor("none")
                    times3 = None
                if datetime.datetime.now().strftime("%d.%m") != awakeDate and iit == 1:
                    times3 = (datetime.datetime.now() + datetime.timedelta(seconds=10)).strftime("%H:%M:%S")
    try:
        checkColor()
    except IOError:
        print("color file unavailable")
