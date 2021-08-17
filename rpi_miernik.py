#zamienic sciezke na zmienna path

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import gpiozero
import datetime

notConnected = False
path = r"data/buffer.txt"

print("mierniksennosci 6.0")

#laczenie z sheets api
scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
loginy = ServiceAccountCredentials.from_json_keyfile_name(r"/home/pi/mierniksennosci/apikey.json", scope)

try:
    client = gspread.authorize(loginy)
    aDane = client.open("Sen").sheet1
    print("Polaczono z Google Sheets API")
except:
    print("Brak polaczenia sieciowego")
    notConnected = True

#gpio setup
b1 = gpiozero.Button(17)
b2 = gpiozero.Button(18)
b3 = gpiozero.Button(4)
l1 = gpiozero.LED(19)
bz1 = gpiozero.Buzzer(21) #cichy
bz2 = gpiozero.Buzzer(25) #glosny
rl1 = gpiozero.OutputDevice(23, False)

def zasnij(czas=datetime.datetime.now().strftime("%H:%M:%S"), data=datetime.datetime.now().strftime("%d.%m.%Y")):
    val = [data, czas, czas]
    aDane.insert_row(val, 2, "USER_ENTERED")
    print(aDane.row_values(2))
    time.sleep(0.5)

def checkConnection():
    global notConnected, aDane, client
    if notConnected:
        try:
            print("Proba nawiazania polaczenia")
            client = gspread.authorize(loginy)
            aDane = client.open("Sen").sheet1
            notConnected = False
            print("proba udana")
        except:
            print("proba nieudana")
            return False
    try:
        aDane.row_values(1)
        return True
    except:
        return False

def addZasnij():
    with open(r"data/buffer.txt", "r+") as f:
        data = f.readlines()
        now = datetime.datetime.now()
        data.extend(["zasnij\n", now.strftime("%d.%m.%Y\n"), now.strftime("%H:%M:%S\n"), now.strftime("%H:%M:%S\n")])
        f.writelines(data)

def checkBuffer():
    with open(r"data/buffer.txt", "r") as f:
        converteddata = []

        data = f.readlines()

    while data:
        if data[0].rstrip("\n") == "zasnij":
            for i in data[1:4]:
                converteddata.append(i.strip())
            aDane.insert_row(converteddata, 2, "USER_ENTERED")

        elif data[0]
#main loop
while 1:
    if b1.is_active:
        checkBuffer()
        if checkConnection():
            zasnij()
        else:
            addZasnij()
    if b2.is_active:
        continue
    if b3.is_active:
        continue