import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import webbrowser
import gpiozero
import time

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
loginy = ServiceAccountCredentials.from_json_keyfile_name("apikey.json", scope)
client = gspread.authorize(loginy)
aDane = client.open("Sen").sheet1
aStats = client.open("Sen").get_worksheet(1)
aSny =  client.open("Sen").get_worksheet(2)
undo = []

b1 = gpiozero.Button(17)
b2 = gpiozero.Button(18)
l1 = gpiozero.LED(19)

l1.off()

def zasnij():
        l1.on()
        czas = datetime.datetime.now().strftime("%H:%M:%S")
        data = datetime.datetime.now().strftime("%d.%m.%Y")

        wartosc = [data, czas, czas]
        aDane.insert_row(wartosc, 2, "USER_ENTERED") #typ danych
        print(aDane.row_values(2))
        b1.wait_for_release()
        l1.off()
def obudzsie():
    try:
        l1.on()
        czas = datetime.datetime.now().strftime("%H:%M:%S")

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
        
        try:
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
        l1.off()
    except:
        l1.off()
        time.sleep(0.5)
        l1.on()
        time.sleep(0.5)
        l1.off
print(":/> ")

while True:
    if b1.is_pressed:
        print("zasnij")
        zasnij()
    if b2.is_pressed:
        print("obudzsie")
        obudzsie()