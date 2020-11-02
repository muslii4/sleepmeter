from flask import Flask, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

app = Flask(__name__)

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
loginy = ServiceAccountCredentials.from_json_keyfile_name("apikey.json", scope)
client = gspread.authorize(loginy)
aDane = client.open("Sen").sheet1
aStats = client.open("Sen").get_worksheet(1)

@app.route("/<inpp>")
def index(inpp):
    print("dziala")
    if inpp == "slp":
        zasnij()
    return render_template('')

def zasnij():
    czas = datetime.datetime.now().strftime("%H:%M:%S")
    data = datetime.datetime.now().strftime("%d.%m.%Y")
    
    wartosc = [data, czas, czas]
    aDane.insert_row(wartosc, 2, "USER_ENTERED") #typ danych
    print(aDane.row_values(2))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=79, debug=True)

while True:
    try:
        inp = input("Co chcesz zrobić? (slp, wu, koniec, del, dlm, getgz, srednia, sny): ")
    except KeyboardInterrupt:
        print("żegnaj")
        break

    czas = datetime.datetime.now().strftime("%H:%M:%S")
    data = datetime.datetime.now().strftime("%d.%m.%Y")

    if inp == "slp":
        zasnij()
    elif inp == "wu":
        wartosc = "=JEŻELI(D2-C2>=0; D2-C2; D2-C2+1)" #żeby nie było ujemnie, 1 = 24hs
        aDane.update_cell(2, 4, czas)
        aDane.update_cell(2, 5, wartosc)
        print(aDane.row_values(2))
    elif inp == "koniec":
        print("żegnaj")
        break
    elif inp == "del":
        print(aDane.row_values(2))
        aDane.delete_row(2)
        print(aDane.row_values(2))
    elif inp == "dlm":
        komorka = aDane.cell(2, 3).value

        godzina = ""
        minuta = ""
        sekunda = ""

        try:
            delay = int(input("Wpisz opóźnienie w minutach: "))
        except ValueError:
            print("używając liczb całkowitych")
            continue
        
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
    elif inp == "getgz":
        print(aDane.cell(2, 3).value)
    elif inp == "srednia":
        print(aStats.cell(1, 2).value)
    elif inp == "sny":
        sen = input("Wpisz co chcesz wpisać (w jak najkrótszej wersji): ")
        aDane.update_cell(2, 6, sen)
    else:
        print("nie.")
