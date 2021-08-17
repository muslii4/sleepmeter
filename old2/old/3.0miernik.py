import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import webbrowser
import gpiozero
import time
import urllib3

# witam, andrzej

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
loginy = ServiceAccountCredentials.from_json_keyfile_name(r"/home/pi/mierniksennosci/apikey.json", scope)
client = gspread.authorize(loginy)
aDane = client.open("Sen").sheet1
aStats = client.open("Sen").get_worksheet(1)
aSny =  client.open("Sen").get_worksheet(2)
allBuffered = False
skip = False

b1 = gpiozero.Button(17)
b2 = gpiozero.Button(18)
l1 = gpiozero.LED(19)
bz1 = gpiozero.Buzzer(21)

czasy1 = ["1.07:50:00", "2.05:55:00", "3.06:50:00", "4.06:50:00", "5.09:10:00"]
czasy2 = ["1.08:13:00", "2.06:23:00", "3.07:13:00", "4.07:13:00", "5.09:43:00"]
sciezka = r"/home/pi/mierniksennosci/buffered.txt"

def pisk(czas, powtorzenia):
    for i in range(powtorzenia):
        bz1.on()
        time.sleep(czas)
        bz1.off()
        if i+1 == powtorzenia:
            print("pisk")
        else:
            time.sleep(czas)
            print("piiisk")

def doSkip():
    pisk(0.05, 2)
    global skip
    skip = not skip
    if skip:
        print("pominięto następny alarm. aby anulować pominięcie naciśnij przyciski jeszcze raz.")
    else:
        print("anulowano nadchodzące pominięcie")
    b1.wait_for_inactive()
    b2.wait_for_inactive()
    time.sleep(0.2)

def juzCzas():
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
    print("wpiszBuffer")
    with open(sciezka, "r") as f:
        content = f.readlines()
    print("Content: ", content)
    if content:
        if content[0].rstrip("\n") == "zasnij":
            print("wpisuje element: zasnij")
            aDane.insert_row([content[1].rstrip("\n"), content[2].rstrip("\n"), content[3].rstrip("\n")], 2, "USER_ENTERED")
            print("wpisane dane: ", aDane.row_values(2))
            with open(sciezka,"w") as f2:
                f2.truncate(0)
                f2.writelines(content[4:])
            with open(sciezka, "r") as f3:
                content = f3.readlines()
            print("Content2:", content)
    if content:
        if content[0].rstrip("\n") == "obudzsie":
            print("wpisuje element: obudzsie")
            obudzsie(content[1])    
            with open(sciezka,"w") as f4:
                f4.truncate(0)
                f4.writelines(content[2:])
    if content:
        if content[0].rstrip("\n") != "obudzsie" and content[0].rstrip("\n") != "zasnij":
            print("Nieprawidłowa linia: ", content[0], "\nusuwanie")
            with open(sciezka, "r+") as f5:
                content = f5.readlines()
                f5.truncate(0)
                f5.writelines(content[1:])
    if not content:
        global allBuffered
        allBuffered = True
        print("wpisywanie zakonczone")
        print("===============================")
    else:
        print("-------------------------------")

def connectionTest():
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
        b1.wait_for_release()

def obudzsie(czas):
    try:
        wartosc = "=JEŻELI(D2-C2>=0; D2-C2; D2-C2+1)" #żeby nie było ujemnie, 1 = 24hs
        aDane.update_cell(2, 4, czas)
        aDane.update_cell(2, 5, wartosc)
        wartosc = "=JEŻELI(B2<=0,5;B2+1;B2)"
        aDane.update_cell(2, 6, wartosc)
        wartosc = "=JEŻELI(C2<=0,5;C2+1;C2)"
        aDane.update_cell(2, 7, wartosc)
        wartosc = "=JEŻELI(B2>0,5;A2;A2-1)"
        aDane.update_cell(2, 8, wartosc)
        print(aDane.row_values(2))
        print("Godzina łóżkowania: " + aDane.cell(2, 2).value)
        komorka = aDane.cell(2, 2).value

        godzina = ""
        minuta = ""
        sekunda = ""

        delay = 15
    
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
    print("zmieniono na " + aDane.cell(2, 3).value)

l1.on()
pisk(0.1, 3)

print("===============================")

if connectionTest():
    while allBuffered == False:
        print("rozpoczynam probe wpisania danych")
        wpiszBuffer()

while True:
    if b1.is_pressed:
        time.sleep(0.5)
        if b2.is_pressed:
            doSkip()
            print("doskip")
            continue
        l1.on()
        print("zasnij")
        pisk(0.1, 1)
        if connectionTest():
            while allBuffered == False:
                print("nie wszystkie dane zostaly wpisane, ponawiam")
                wpiszBuffer()
            zasnij()
            pisk(0.2, 2)
        else:
            print("połączenie sieciowe niedostępne, zapisywanie w pamięci")
            dopiszZasnij()
            pisk(0.5, 1)
        l1.off()
        b1.wait_for_release()
        print("===============================")
    elif b2.is_pressed:
        time.sleep(0.5)
        if b1.is_pressed:
            doSkip()
            print("doskip")
            continue
        l1.on()
        print("obudzsie")
        pisk(0.1, 1)
        if connectionTest():
            while allBuffered == False:
                print("nie wszystkie dane zostaly wpisane, ponawiam")
                wpiszBuffer()
            obudzsie(datetime.datetime.now().strftime("%H:%M:%S"))    
            pisk(0.2, 2)
        else:
            print("połączenie sieciowe niedostępne, zapisywanie w pamięci")
            dopiszObudzsie()
            pisk(0.5, 1)    
        l1.off()
        print("===============================")
    else:
        if juzCzas() == 1:
            if skip == False:
                bz1.on()
                b1.wait_for_press()
                bz1.off()
                b1.wait_for_inactive()
                print("alarm wyłączony")
                time.sleep(0.5)
            else:
                skip = False
                print("alarm anulowany, pominięto")
                time.sleep(1)
        if juzCzas() == 2:
            if skip == False:
                while b1.is_pressed == 0:
                    bz1.on()
                    time.sleep(1)
                    bz1.off()
                    time.sleep(0.5)
                b1.wait_for_inactive()
                print("alarm wyłączony")
                time.sleep(0.5)
            else:
                skip = False
                print("alarm anulowany, pominięto")
                time.sleep(1)