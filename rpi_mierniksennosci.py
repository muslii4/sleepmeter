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

# sudo nano /etc/xdg/autostart/miernik.desktop

# TODO:
#  - config file
#  - tlumaczenie na ang
#
#  - cos z ld ale nikt nie wie co
#  - podejrzanie dlugie obliczenia w obudzsie
#  - ta delta jeszcze niepewna taka

with open("config.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

budzikLinki = config["budzik"]["ytLista"]

allBuffered = False
skip = False
jestZle = False
dataObudzenia = 0

holidaysStart = datetime.datetime.strptime(config["holidays"]["holidaysStart"], "%d.%m.%Y")
holidaysEnd = datetime.datetime.strptime(config["holidays"]["holidaysEnd"], "%d.%m.%Y")

sun = suntime.Sun(config["led"]["lat"], config["led"]["lon"])
utc = pytz.UTC

sleepDelay = config["budzik"]["sleepDelay"]

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
loginy = ServiceAccountCredentials.from_json_keyfile_name(r"/home/pi/mierniksennosci/data/apikey.json", scope)

print("mierniksennosci v5.5 gpiorpi")

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
    client = gspread.authorize(loginy)
    aDane = client.open("Sen").sheet1
except:
    print("Tryb offline")
    jestZle = True

b1 = gpiozero.Button(13)
b2 = gpiozero.Button(6)
b3 = gpiozero.Button(10)
b4 = gpiozero.Button(11)
l1 = gpiozero.LED(26)
l2 = gpiozero.LED(9)
bz1 = gpiozero.Buzzer(5) #cichy
bz2 = gpiozero.Buzzer(19) #glosny
bz3 = gpiozero.TonalBuzzer(27)
rl1 = gpiozero.OutputDevice(21, False)

czasyStacjonarne = config["budzik"]["czasy"]["stacjonarne"] # 0=monday
czasyZdalne = config["budzik"]["czasy"]["zdalne"]
czasy1optimized = None
czasy2 = None
czasy3 = None
buffer = r"/home/pi/mierniksennosci/data/buffer.txt"

if config["budzik"]["czasy"]["aktualnie"] == "zdalne":
    czasy1 = czasyZdalne
elif config["budzik"]["czasy"]["aktualne"] == "stacjonarne":
    czasy1 = czasyStacjonarne
else:
    raise ValueError("nie podano czasu")

def optimizeAlarms(): # zoptymalizowane sa troche wczesniej niz zwykle ale tamte tez wystepuja
    global czasy1, czasy1optimized
    now = datetime.datetime.now()
    if now.hour < 12:
        nextWeekday = now.weekday()
    else:
        nextWeekday = now.weekday() + 1
    if nextWeekday == 7:
        nextWeekday = 0
    
    nextAlarm = None
    for i in range(len(czasy1)):
        if czasy1[i][:1] == str(nextWeekday):
            nextAlarm = datetime.datetime.strptime(czasy1[i], "%U.%H:%M:%S")
            alarmBefore = czasy1[i]
            break
    if nextAlarm == None:
        print("brak alarmu do zoptymalizowania")
        return 0

    timeToAlarm = (nextAlarm - now).seconds/(60*60) - (sleepDelay/60) # to decimal hours
    perfectDelta = timeToAlarm % 1.5 # perfect sleep = divisible by 1.5h

    if perfectDelta < config["budzik"]["maxOptymalizacja"]:
        czasy1optimized = nextWeekday + (now + datetime.timedelta(hours=timeToAlarm-perfectDelta)).strftime(".%H:%M:%S")
        print("zoptymalizowano alarm", alarmBefore, "do", czasy1optimized)
    else:
        print("nie zoptymalizowano alarmu")

    print("delta min:", perfectDelta*60)

def checkColor():
    global setColor
    with open(config["led"]["file"], "r+") as f:
        try:
            val = f.read().strip("\n")[-9:]
        except:
            return None
    if val != setColor:
        if val == "000000000":
            ledkolor("none")
            rl1.off()
        else:
            ledkolor(val)
            rl1.on()

def whiteTone():
    if sun.get_local_sunrise_time() < utc.localize(datetime.datetime.now()) < sun.get_local_sunset_time(): # czy jest miedzy wschodem a zachodem slonca
        return "255255255" # bardzo bialy
    else:
        return "lowblue" # cieply bialy

def ledkolor(kolor):
    global setColor
    if kolor == "highblue":
        kolor = config["led"]["colors"]["highblue"]
    if kolor == "lowblue":
        kolor = config["led"]["colors"]["lowblue"]
    if kolor == "none":
        kolor = "000000000"
    
    ser.write(kolor.encode())
    setColor = kolor
    with open(config["led"]["file"], "w") as f:
        f.write(kolor)

def youtubowyBudzik():
    global budzikLinki
    rl1.on()
    ledkolor("highblue")
    webbrowser.get("chromium-browser").open_new_tab("http://www.hasthelargehadroncolliderdestroyedtheworldyet.com/") # bez tego nie ma autoplay na yt ze wzgledu na powody
    time.sleep(2)
    webbrowser.get("chromium-browser").open_new_tab(budzikLinki[random.randint(0, len(budzikLinki) - 1)])
    koniec = datetime.datetime.now() + datetime.timedelta(minutes=3)
    while 1:
        if datetime.datetime.now() >= koniec:
            os.system("pkill -f chromium")
            pisk(0.1, 2, bz2)
            while datetime.datetime.now() <= koniec:
                if b1.is_active:
                    break
                if b2.is_active:
                    bz2.off()
                    return 0
            if not b1.is_active:
                ledkolor("255000000")
                bz2.on()
                b1.wait_for_press()
                ledkolor("lowblue")
                bz2.off()
                time.sleep(0.5)
            b1.wait_for_inactive()
            print("alarm wylaczony")
            time.sleep(1)
            rl1.off()
            ledkolor("none")
            break
        elif b1.is_active == 1:
            print("alarm wylaczony")
            time.sleep(1)
            rl1.off()
            ledkolor("none")
            os.system("pkill -f chromium")
            break
            
def pisk(czas, powtorzenia, bz):
    for i in range(powtorzenia):
        bz.on()
        time.sleep(czas)
        bz.off()
        if i+1 != powtorzenia:
            time.sleep(czas)

def doSkip():
    pisk(0.05, 2, bz2)
    global skip
    skip = not skip
    if skip:
        print("pominieto nastepny alarm")
    else:
        print("anulowano pominiecie")
    time.sleep(0.2)
    b1.wait_for_inactive()
    b2.wait_for_inactive()

def juzCzas():
    global czasy1, czasy2, czasy3
    now = time.strftime("%U.%H:%M:%S")

    if now in czasy1: # planowane
        return 1
    elif now == czasy1optimized: # planowane.optimized
        return 1.5
    elif now == czasy2: # 6godzinne
        return 2
    elif now == czasy3: # 10sekundowe przymuszenie do wstania, nie dziala na 6godzinne ale to pozniej pisze
        return 3
    else:
        return 0
            
def dopiszZasnij():
    global allBuffered
    with open(buffer, "r") as f:
        content = f.readlines()
    with open(buffer, "w") as f2:
        lines = ["zasnij\n", datetime.datetime.now().strftime("%d.%m.%Y\n"), datetime.datetime.now().strftime("%H:%M:%S\n"), datetime.datetime.now().strftime("%H:%M:%S\n")]
        f2.writelines(content + lines)
    
    time.sleep(0.5)
    l1.off()
    time.sleep(0.5)
    l1.on()
    time.sleep(0.5)
    
    allBuffered = False

def dopiszObudzsie():
    global allBuffered
    with open(buffer, "r") as f:
        content = f.readlines()
    with open(buffer, "w") as f2:
        lines = ["obudzsie\n", datetime.datetime.now().strftime("%H:%M:%S\n")]
        f2.writelines(content + lines)
    
    time.sleep(0.5)
    l1.off()
    time.sleep(0.5)
    l1.on()
    time.sleep(0.5)

    allBuffered = False

def wpiszBuffer():
    time.sleep(0.2)
    l1.off()
    time.sleep(0.2)
    l1.on()
    time.sleep(0.2)
    with open(buffer, "r") as f:
        content = f.readlines()
    if content:
        if content[0].rstrip("\n") == "zasnij":
            aDane.insert_row([content[1].rstrip("\n"), content[2].rstrip("\n"), content[3].rstrip("\n")], 2, "USER_ENTERED")
            with open(buffer,"w") as f2:
                f2.truncate(0)
                f2.writelines(content[4:])
            with open(buffer, "r") as f3:
                content = f3.readlines()
    if content:
        if content[0].rstrip("\n") == "obudzsie":
            obudzsie(content[1], True)    
            with open(buffer,"w") as f4:
                f4.truncate(0)
                f4.writelines(content[2:])
    if content:
        if content[0].rstrip("\n") != "obudzsie" and content[0].rstrip("\n") != "zasnij":
            print("Nieprawidlowa linia: ", content[0], "\nusuwanie")
            with open(buffer, "r+") as f5:
                content = f5.readlines()
                f5.truncate(0)
                f5.writelines(content[1:])
    if not content:
        global allBuffered
        allBuffered = True

def connectionTest():
    global jestZle, aDane, client
    if jestZle:
        try:
            client = gspread.authorize(loginy)
            aDane = client.open("Sen").sheet1
            jestZle = False
            print("proba nawiazania polaczenia udana")
        except:
            print("proba nawiazania polaczenia nieudana")
            return False
    try:
        url = "https://www.google.com/"
        conn = urllib3.connection_from_url(url)
        conn.request("GET", "/")
        return True
    except:
        return False

def zasnij():
        czas = datetime.datetime.now().strftime("%H:%M:%S")
        data = datetime.datetime.now().strftime("%d.%m.%Y")

        wartosc = [data, czas, czas]
        aDane.insert_row(wartosc, 2, "USER_ENTERED") #typ danych
        print(aDane.row_values(2))
        time.sleep(0.5)
        b1.wait_for_inactive()

def obudzsie(czas, sztuczne):
    global dataObudzenia, sleepDelay

    if not sztuczne and len(sys.argv) < 2: # dowolny argument to wylacza
        bz2.on()
        n = str(input("podaj dzisiejsza liczbe: "))
        while n != str(((datetime.datetime.now().timetuple().tm_yday + 1) ** 20))[:6]:
            n = str(input("podaj dzisiejsza liczbe: "))
        bz2.off()

    try:
        wartosc = "=IF(D2-C2>=0; D2-C2; D2-C2+1)" #zeby nie bylo ujemnie, 1 = 24hs
        aDane.update_cell(2, 4, czas)
        aDane.update_cell(2, 5, wartosc)
        wartosc = "=IF(B2<=0,5;B2+1;B2)"
        aDane.update_cell(2, 6, wartosc)
        wartosc = "=IF(C2<=0,5;C2+1;C2)"
        aDane.update_cell(2, 7, wartosc)
        wartosc = "=IF(B2>0,5;A2;A2-1)"
        aDane.update_cell(2, 8, wartosc)
        komorka = aDane.cell(2, 2).value

        godzina = ""
        minuta = ""
        sekunda = ""
    
        godzina = godzina + komorka[0]
        godzina = godzina + komorka[1]
        godzina = int(godzina)

        minuta = minuta + komorka[3]
        minuta = minuta + komorka[4]
        minuta = int(minuta)

        sekunda = sekunda + komorka[6]
        sekunda = sekunda + komorka[7]
        sekunda = int(sekunda)
    except ValueError:
        print("problem")

    wartosc = str(godzina) + ":" + str(minuta + sleepDelay) + ":" + str(sekunda)
    
    aDane.update_cell(2, 3, wartosc)
    dataObudzenia = datetime.datetime.now().strftime("%d.%m")

if connectionTest():
    while allBuffered == False:
        wpiszBuffer()

rl1.off()
l1.on()
pisk(0.1, 3, bz1)

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
            print("sen szesciogodzinny")
            czasy2 = (datetime.datetime.now() + datetime.timedelta(hours=6,minutes=sleepDelay)).strftime("%H:%M:%S")
            print(czasy2)
            pisk(0.1, 1, bz1)
        else:
            czasy2 = None # 6godzinne mozna anulowac naciskajac zasnij jeszcze raz
        l1.off()
        ledkolor("lowblue")
        print("zasnij")
        pisk(0.1, 1, bz1)
        if connectionTest():
            while allBuffered == False:
                wpiszBuffer()
            zasnij()
            pisk(0.2, 2, bz1)
        else:
            print("zapisywanie offline")
            ledkolor("lowblue")
            dopiszZasnij()
            pisk(0.5, 1, bz1)
        time.sleep(0.5)
        b1.wait_for_inactive()
        optimizeAlarms()
        print("===============================")
        time.sleep(5)
        rl1.off()
        l1.on()
        ledkolor("none")
    elif b2.is_pressed:
        rl1.on()
        time.sleep(0.5)
        if b1.is_pressed:
            doSkip()
            time.sleep(3)
            rl1.off()
            continue
        l1.off()
        ledkolor("highblue")
        print("obudzsie")
        pisk(0.1, 1, bz2)
        if connectionTest():
            while allBuffered == False:
                wpiszBuffer()
            obudzsie(datetime.datetime.now().strftime("%H:%M:%S"), False)
            pisk(0.2, 2, bz1)
            webbrowser.get("chromium-browser").open_new_tab("meteo.pl/um/php/meteorogram_id_um.php?ntype=0u&id=686")
            time.sleep(60)
            os.system("pkill -f chromium")
        else:
            print("zapisywanie offline")
            ledkolor("255000000")
            dopiszObudzsie()
            pisk(0.5, 1, bz1)    
        czasy2 = None
        czasy3 = None
        print("===============================")
        time.sleep(3)
        rl1.off()
        l1.on()
        ledkolor("none")
    elif b3.is_pressed:
        rl1.toggle()
        if rl1.is_active:
            ledkolor(whiteTone())
        else:
            ledkolor("none")
        time.sleep(0.5)
        if b3.is_pressed:
            if not rl1.is_active:
                time.sleep(0.5)
                ledkolor(whiteTone())
                rl1.on()
            selcolor = input("Wpisz kolor (255255255): ")
            ledkolor(str(selcolor))
    else:
        jc = juzCzas()
        
        if jc > 0 :
            if skip == True:
                if jc != 1.5: # zoptymalizowane powinny byc pomijane razem ze standardowymi
                    skip = False
                print("pominieto #" + jc)
                time.sleep(1)
            elif holidaysStart <= datetime.datetime.now() <= holidaysEnd and jc != 2: # 6godzinne powinny dzialac w wakacje, 10s nie wystapia
                print("wakacje, pominieto alarm")
                time.sleep(1)
            elif datetime.datetime.now().strftime("%d.%m") == dataObudzenia:
                czasy2 = None
                czasy3 = None
            else:
                if jc == 1:
                    youtubowyBudzik()
                elif jc == 1.5:
                    print("alarm zoptymalizowany")
                    youtubowyBudzik()
                elif jc == 2:
                    print("alarm szesciogodzinny")
                    youtubowyBudzik()
                elif jc == 3:
                    ledkolor("255000000")
                    rl1.on()
                    bz2.on()
                    time.sleep(1)
                    b1.wait_for_press()
                    bz2.off()
                    time.sleep(0.5)
                    b1.wait_for_inactive()
                    time.sleep(1)
                    rl1.off()
                    ledkolor("none")
                    czasy3 = None
                if datetime.datetime.now().strftime("%d.%m") != dataObudzenia and jc == 1: #6godzinne mozna odpuscic bo potem nie dzialaja inne
                    czasy3 = (datetime.datetime.now() + datetime.timedelta(seconds=10)).strftime("%H:%M:%S")
    try:
        checkColor()
    except IOError:
        print("color file unavailable")
