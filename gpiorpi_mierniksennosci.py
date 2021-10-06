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

# sudo nano /etc/xdg/autostart/miernik.desktop

budzikLinki = ["https://www.youtube.com/watch?v=xJiaTpmeTX4", # su lee - wide awake
               "https://www.youtube.com/watch?v=-dkdi-tCEw0", # su lee - sleepy hollow
               "https://www.youtube.com/watch?v=BVVfMFS3mgc", # chuu loona - heart attack
               "https://www.youtube.com/watch?v=ainyK6fXku0", # william shatner - common people
               "https://www.youtube.com/watch?v=nso6Vhg0p9k", # szanty - bitwa
               "https://www.youtube.com/watch?v=6M4d2SmhSP8", # yvette young - a map a string a light
               "https://www.youtube.com/watch?v=_xR2BymJj6U", # daria zawialow - hej hej
               "https://www.youtube.com/watch?v=M2QSMMXKQxE", # aseul - sandcastles
               "https://www.youtube.com/watch?v=CYiGyaJyPMk", # young leosia - szklanki
               "https://www.youtube.com/watch?v=f_6AQA4uzD0"  # preubens gloria
               ]

allBuffered = False
skip = False
jestZle = False
dataObudzenia = 0

holidaysStart = datetime.datetime(day=29,month=12,year=2020)
holidaysEnd = datetime.datetime(day=17,month=1,year=2021)

lat = 49.8
lon = 19
sun = suntime.Sun(lat, lon)
utc = pytz.UTC

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
loginy = ServiceAccountCredentials.from_json_keyfile_name(r"/home/pi/mierniksennosci/apikey.json", scope)

print("mierniksennosci v5.4 gpiorpi")

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
ser.flush()

ser.write("255000000".encode())
line = ser.readline().decode('utf-8').rstrip()
time.sleep(1.2)
ser.write("000255000".encode())
line = ser.readline().decode('utf-8').rstrip()
time.sleep(1.2)
ser.write("000000255".encode())
line = ser.readline().decode('utf-8').rstrip()
time.sleep(1.2)
ser.write("000000000".encode())
line = ser.readline().decode('utf-8').rstrip()

setColor = "000000000"

try:
    client = gspread.authorize(loginy)
    aDane = client.open("Sen").sheet1
except:
    print("Brak polaczenia sieciowego, program zostanie uruchomiony w trybie offline")
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

czasy1 = ["1.08:00:00", "2.06:52:00", "3.06:52:00", "4.06:52:00", "5.06:52:00"]
czasy2 = ["1.08:54:00", "2.07:09:00", "3.07:09:00", "4.07:09:00", "5.07:09:00"]
czasy3 = 0
czasy4 = 0
odjazdy = ["09:05", "07:20", "07:20", "07:20", "07:20"]
sciezka = r"/home/pi/mierniksennosci/data/buffer.txt"

def checkColor():
    global setColor
    with open(r"/var/lib/docker/volumes/homeassistant/_data/sensor.txt", "r+") as f:
        try:
            val = f.read().strip("\n")[-9:]
        except:
            return None
    if val != setColor:
        if val == "000000000":
            ledkolor(val)
            rl1.off()
        else:
            ledkolor(val)
            rl1.on()

def whiteTone():
    if sun.get_local_sunrise_time() < utc.localize(datetime.datetime.now()) < sun.get_local_sunset_time(): # czy jest miedzy wschodem a zachodem slonca
        return "255255255" # bardzo bialy
    else:
        return "173088014" # cieply bialy

def ledkolor(kolor):
    global setColor
    ser.write(kolor.encode())
    setColor = kolor
    line = ser.readline().decode('utf-8').rstrip()

    with open(r"/var/lib/docker/volumes/homeassistant/_data/sensor.txt", "w") as f:
        f.write(kolor)

def youtubowyBudzik(jc):
    global budzikLinki
    rl1.on()
    ledkolor("056232255")
    webbrowser.get("chromium-browser").open_new_tab("http://www.hasthelargehadroncolliderdestroyedtheworldyet.com/")
    time.sleep(2)
    webbrowser.get("chromium-browser").open_new_tab(budzikLinki[random.randint(0, len(budzikLinki) - 1)])
    koniec = datetime.datetime.now() + datetime.timedelta(minutes=3)
    while 1:
        if datetime.datetime.now() >= koniec:
            os.system("pkill -f chromium")
            pisk(0.1, 2, bz2)
            if jc != 3:
                koniec = datetime.datetime.now() + datetime.timedelta(seconds=3)
            while datetime.datetime.now() <= koniec:
                if b1.is_active:
                    break
            if not b1.is_active:
                ledkolor("255000000")
                bz2.on()
                b1.wait_for_press()
                ledkolor("056232255")
                bz2.off()
                time.sleep(0.5)
            b1.wait_for_inactive()
            print("alarm wylaczony")
            time.sleep(1)
            rl1.off()
            ledkolor("000000000")
            break
        elif b1.is_active == 1:
            print("alarm wylaczony")
            time.sleep(1)
            rl1.off()
            ledkolor("000000000")
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
        print("pominieto nastepny alarm. aby anulowac pominiecie nacisnij przyciski jeszcze raz.")
    else:
        print("anulowano nadchodzace pominiecie")
    time.sleep(0.2)
    b1.wait_for_inactive()
    b2.wait_for_inactive()

def juzCzas():
    global czasy3, czasy4
    try:
        print("index czasu:", czasy1.index(time.strftime("%u.%H:%M:%S")))
        print("lista 1")
        return 1
    except ValueError:
        try:
            print("index czasu:", czasy2.index(time.strftime("%u.%H:%M:%S")))
            print("lista 2")
            return 2
        except ValueError:
            if czasy3 == datetime.datetime.now().strftime("%H:%M:%S"):
                czasy3 = 0
                return 3
            else:
                if czasy4 == datetime.datetime.now().strftime("%H:%M:%S"):
                    czasy4 = 0
                    return 4
                else:
                    return 0
            
def dopiszZasnij():
    global allBuffered
    with open(sciezka, "r") as f:
        content = f.readlines()
    with open(sciezka, "w") as f2:
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
    with open(sciezka, "r") as f:
        content = f.readlines()
    with open(sciezka, "w") as f2:
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
    with open(sciezka, "r") as f:
        content = f.readlines()
    print("Content: ", content)
    if content:
        if content[0].rstrip("\n") == "zasnij":
            aDane.insert_row([content[1].rstrip("\n"), content[2].rstrip("\n"), content[3].rstrip("\n")], 2, "USER_ENTERED")
            with open(sciezka,"w") as f2:
                f2.truncate(0)
                f2.writelines(content[4:])
            with open(sciezka, "r") as f3:
                content = f3.readlines()
    if content:
        if content[0].rstrip("\n") == "obudzsie":
            obudzsie(content[1], True)    
            with open(sciezka,"w") as f4:
                f4.truncate(0)
                f4.writelines(content[2:])
    if content:
        if content[0].rstrip("\n") != "obudzsie" and content[0].rstrip("\n") != "zasnij":
            print("Nieprawidlowa linia: ", content[0], "\nusuwanie")
            with open(sciezka, "r+") as f5:
                content = f5.readlines()
                f5.truncate(0)
                f5.writelines(content[1:])
    if not content:
        global allBuffered
        allBuffered = True
    else:
        print("-------------------------------")

def connectionTest():
    global jestZle, aDane, client
    if jestZle:
        try:
            print("proba nawiazania polaczenia")
            client = gspread.authorize(loginy)
            aDane = client.open("Sen").sheet1
            jestZle = False
            print("sukces")
        except:
            print("porazka")
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
    global dataObudzenia

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

        delay = 10
    
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

    wartosc = str(godzina) + ":" + str(minuta + delay) + ":" + str(sekunda)
    
    aDane.update_cell(2, 3, wartosc)
    dataObudzenia = datetime.datetime.now().strftime("%d.%m")
    print("dzisiejsze alarmy anulowane")

rl1.off()
l1.on()
pisk(0.1, 3, bz1)

if connectionTest():
    while allBuffered == False:
        wpiszBuffer()

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
            czasy3 = (datetime.datetime.now() + datetime.timedelta(hours=6,minutes=15)).strftime("%H:%M:%S")
            print(czasy3)
            pisk(0.1, 1, bz1)
        l1.off()
        ledkolor("173088014")
        print("zasnij")
        pisk(0.1, 1, bz1)
        if connectionTest():
            while allBuffered == False:
                wpiszBuffer()
            zasnij()
            pisk(0.2, 2, bz1)
        else:
            print("polaczenie sieciowe niedostepne, zapisywanie w pamieci")
            ledkolor("056232255")
            dopiszZasnij()
            pisk(0.5, 1, bz1)
        time.sleep(0.5)
        b1.wait_for_inactive()
        print("===============================")
        time.sleep(5)
        rl1.off()
        l1.on()
        ledkolor("000000000")
    elif b2.is_pressed:
        rl1.on()
        time.sleep(0.5)
        if b1.is_pressed:
            doSkip()
            time.sleep(3)
            rl1.off()
            continue
        l1.off()
        ledkolor("056232255")
        print("obudzsie")
        pisk(0.1, 1, bz2)
        if connectionTest():
            while allBuffered == False:
                wpiszBuffer()
            obudzsie(datetime.datetime.now().strftime("%H:%M:%S"), False)
            pisk(0.2, 2, bz1)
            print("pokazuje pogode")
            webbrowser.get("chromium-browser").open_new_tab("meteo.pl/um/php/meteorogram_id_um.php?ntype=0u&id=686")
            time.sleep(60)
            os.system("pkill -f chromium")
        else:
            print("polaczenie sieciowe niedostepne, zapisywanie w pamieci")
            ledkolor("255000000")
            dopiszObudzsie()
            pisk(0.5, 1, bz1)    
        czasy3 = 0
        czasy4 = 0
        print("===============================")
        time.sleep(3)
        rl1.off()
        l1.on()
        ledkolor("000000000")
    elif b3.is_pressed:
        rl1.toggle()
        if rl1.is_active:
            ledkolor(whiteTone())
        else:
            ledkolor("000000000")
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
                skip = False
                print("pominieto #", jc)
                time.sleep(1)
            elif holidaysStart <= datetime.datetime.now() <= holidaysEnd and jc != 3 and jc != 4: # 6godzinne i 10sekundowe powinny dzialac w wakacje
                print("wakacje")
                time.sleep(1)
            elif datetime.datetime.now().strftime("%d.%m") == dataObudzenia:
                czasy3 = 0
                czasy4 = 0
            else:
                if jc == 1:
                    youtubowyBudzik(jc)
                elif jc == 2:
                    ledkolor("255000000")
                    while b1.is_pressed == 0:
                        bz2.on()
                        rl1.on()
                        time.sleep(1)
                        bz2.off()
                        rl1.off()
                        time.sleep(0.5)
                    b1.wait_for_inactive()
                    rl1.on()
                    print("alarm wylaczony")
                    time.sleep(1)
                    rl1.off()
                    ledkolor("000000000")
                elif jc == 3:
                    print("alarm szesciogodzinny")
                    youtubowyBudzik(jc)
                elif jc == 4:
                    print("wstawaj leniu")
                    ledkolor("255000000")
                    rl1.on()
                    bz2.on()
                    time.sleep(1)
                    b1.wait_for_press()
                    bz2.off()
                    time.sleep(0.5)
                    b1.wait_for_inactive()
                    print("alarm wylaczony")
                    time.sleep(1)
                    rl1.off()
                    ledkolor("000000000")
                    czasy4 = 0
                if datetime.datetime.now().strftime("%d.%m") != dataObudzenia and jc != 3: #6godzinne mozna odpuscic bo potem nie dzialaja inne
                    czasy4 = (datetime.datetime.now() + datetime.timedelta(seconds=10)).strftime("%H:%M:%S")
    try:
        checkColor()
    except IOError:
        print("file unavailable")
