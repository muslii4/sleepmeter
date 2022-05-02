from __future__ import division
import time
import datetime
import webbrowser
import os
import gpiozero
import urllib3
import multiprocessing
import lib.configFile as configFile
import lib.ledstrip as ledstrip
import lib.musicPlayer as musicPlayer
import lib.buffer as buffer
import lib.sheetsApi as sheetsApi

# /etc/xdg/autostart/sleepmeter.desktop

# TODO:
#  - lucid dreaming tools
#  - translate cli

def showWeather():
    webbrowser.get(config["alarmClock"]["browser"]).open_new_tab(config["alarmClock"]["weatherURL"])
    time.sleep(60)
    os.system("pkill -f " + config["alarmClock"]["browser"])
    rl1.off()
    l1.off()

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
            nextAlarm = datetime.datetime.strptime(times1[i], "%u.%H:%M:%S")
            alarmBefore = times1[i]
            break
    if nextAlarm == None:
        print("no alarms to optimize")
        return 0

    timeToAlarm = (nextAlarm - now).seconds/(60*60) - (sleepDelay/60) # to decimal hours
    perfectDelta = timeToAlarm % 1.5 # perfect sleep = divisible by 1.5h

    if perfectDelta < config["alarmClock"]["maxOptimization"]:
        times1optimized = str(nextWeekday) + (now + datetime.timedelta(hours=timeToAlarm-perfectDelta)).strftime("%u.%H:%M:%S")
        print("optimized time", alarmBefore, "to", times1optimized)
    else:
        print("alarms did not get optimized")

    print("delta (minutes):", perfectDelta*60)

def musicAlarm():
    global skip
    rl1.on()
    ledstrip.ledColor("highblue")
    player = multiprocessing.Process(target=musicPlayer.playRandomSong)
    player.start()
    while player.is_alive():
        if b1.is_active:
            musicPlayer.killPlayer(player)
            time.sleep(1)
            rl1.off()
            ledstrip.ledColor("none")
            return 0
        if b2.is_active:
            musicPlayer.killPlayer(player)
            skip = True
            print("alarm off")
            time.sleep(1)
            rl1.off()
            ledstrip.ledColor("none")
            return 0
    ledstrip.ledColor("255000000")
    bz2.on()
    b1.wait_for_press()
    ledstrip.ledColor("lowblue")
    bz2.off()
    time.sleep(1)
    rl1.off()
    ledstrip.ledColor("none")
            
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
    now = datetime.datetime.now().strftime("%u.%H:%M:%S")

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

def connectionTest():
    global offlineMode, sheet
    if offlineMode:
        try:
            sheet = sheetsApi.getSheet()
            offlineMode = False
            print("connection attempt successful")
        except:
            print("connection attempt unsuccessful")
            return False
    try:
        url = "https://www.google.com/"
        conn = urllib3.connection_from_url(url)
        conn.request("GET", "/")
        offlineMode = False
        return True
    except:
        offlineMode = True
        return False

def asleep():
        timeVal = datetime.datetime.now().strftime("%H:%M:%S")
        date = datetime.datetime.now().strftime("%d.%m.%Y")

        value = [date, timeVal, timeVal]
        sheet.insert_row(value, 2, "USER_ENTERED")
        print(sheet.row_values(2))
        time.sleep(0.5)
        b1.wait_for_inactive()

def awake(timeVal, fromBuffer, sheet, sleepDelay):
    global awakeDate

    if not fromBuffer and config["askForNumber"]:
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

if __name__ == "__main__":
    skip = False
    offlineMode = False
    awakeDate = 0

    config = configFile.getConfig()
    holidaysStart = datetime.datetime.strptime(config["holidays"]["holidaysStart"], "%d.%m.%Y")
    holidaysEnd = datetime.datetime.strptime(config["holidays"]["holidaysEnd"], "%d.%m.%Y")
    sleepDelay = config["alarmClock"]["sleepDelay"]

    print("sleepmeter v6 gpiorpi")
    ledstrip.init()
    downloader = multiprocessing.Process(target=musicPlayer.updateSongs)
    downloader.start()

    try:
        sheet = sheetsApi.getSheet()
    except:
        print("Offline mode")
        offlineMode = True

    b1 = gpiozero.Button(13)
    b2 = gpiozero.Button(6)
    b3 = gpiozero.Button(10)
    b4 = gpiozero.Button(9)
    l1 = gpiozero.LED(26, False)
    l2 = gpiozero.LED(11, False)
    bz1 = gpiozero.Buzzer(5) # quiet
    bz2 = gpiozero.Buzzer(19) # loud
    bz3 = gpiozero.TonalBuzzer(27)
    rl1 = gpiozero.OutputDevice(21, False)

    times1 = configFile.getTimes1()
    times1optimized = None
    times2 = None
    times3 = None

    if connectionTest():
        saver = multiprocessing.Process(target=buffer.saveBufferOnline)
        saver.start()

    ledstrip.checkColor(rl1)

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
                times2 = (datetime.datetime.now() + datetime.timedelta(hours=6, minutes=sleepDelay)).strftime("%u.%H:%M:%S")
                print(times2)
                beep(0.1, 1, bz1)
            else:
                times2 = None
            l1.on()
            ledstrip.ledColor("lowblue")
            print("asleep")
            beep(0.1, 1, bz1)
            if connectionTest():
                if buffer.isNotEmpty():
                    buffer.saveAsleep()
                    saver = multiprocessing.Process(target=buffer.saveBufferOnline)
                    saver.start()
                else:
                    asleep()
            else:
                print("saving offline")
                ledstrip.ledColor("lowblue")
                buffer.saveAsleep()
            beep(0.2, 2, bz1)
            b1.wait_for_inactive()
            optimizeAlarms()
            print("===============================")
            time.sleep(3)
            rl1.off()
            l1.off()
            ledstrip.ledColor("none")
        elif b2.is_pressed:
            rl1.on()
            time.sleep(0.5)
            if b1.is_pressed:
                doSkip()
                time.sleep(3)
                rl1.off()
                continue
            l1.on()
            ledstrip.ledColor("highblue")
            print("awake")
            beep(0.1, 1, bz2)
            if connectionTest():
                if buffer.isNotEmpty():
                    buffer.saveAwake()
                    saver = multiprocessing.Process(target=buffer.saveBufferOnline)
                    saver.start()
                else:
                    awake(datetime.datetime.now().strftime("%H:%M:%S"), False, sheet, sleepDelay)
                weather = multiprocessing.Process(target=showWeather)
                weather.start()
                beep(0.2, 2, bz1)
            else:
                print("saving offline")
                ledstrip.ledColor("255000000")
                buffer.saveAwake()
                beep(0.2, 2, bz1)
                time.sleep(1)
                rl1.off()
                l1.off()
            times2 = None
            times3 = None
            print("===============================")
            ledstrip.ledColor("none")
        elif b3.is_pressed:
            rl1.toggle()
            if rl1.is_active:
                ledstrip.ledColor(ledstrip.whiteTone())
            else:
                ledstrip.ledColor("none")
            time.sleep(0.5)
            if b3.is_pressed:
                if not rl1.is_active:
                    time.sleep(0.5)
                    ledstrip.ledColor(ledstrip.whiteTone())
                    rl1.on()
                selcolor = input("Enter color value (255255255): ")
                ledstrip.ledColor(str(selcolor))
        elif b4.is_pressed: #lucid dreaming
            pass
        else:
            iit = isItTime()
            
            if iit > 0 :
                if skip == True:
                    if iit != 1.5: # optimized and standard are skipped by one skip
                        skip = False
                    print("skipped #" + iit)
                    time.sleep(1)
                elif holidaysStart <= datetime.datetime.now() <= holidaysEnd and iit != 2:
                    print("holidays, skipping alarm")
                    time.sleep(1)
                elif datetime.datetime.now().strftime("%d.%m") == awakeDate:
                    times2 = None
                    times3 = None
                else:
                    if iit == 1:
                        musicAlarm()
                    elif iit == 1.5:
                        print("optimized alarm")
                        musicAlarm()
                    elif iit == 2:
                        print("6h alarm")
                        musicAlarm()
                    elif iit == 3:
                        ledstrip.ledColor("255000000")
                        rl1.on()
                        bz2.on()
                        time.sleep(1)
                        b1.wait_for_press()
                        bz2.off()
                        time.sleep(0.5)
                        b1.wait_for_inactive()
                        time.sleep(1)
                        rl1.off()
                        ledstrip.ledColor("none")
                        times3 = None
                    if datetime.datetime.now().strftime("%d.%m") != awakeDate and (iit == 1 or iit == 1.5) and not skip:
                        times3 = (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime("%u.%H:%M:%S")
                        print("next alarm in 5 minutes")
                    elif skip:
                        skip = False
        try:
            ledstrip.checkColor(rl1)
        except IOError:
            print("color file unavailable")
