import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import webbrowser
import time
import urllib3
from random import randint

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
loginy = ServiceAccountCredentials.from_json_keyfile_name(r"apikey.json", scope)
client = gspread.authorize(loginy)
aDane = client.open("Sen").sheet1

for i in range(10):
    godzina = randint(23, 24)
    minuta = randint(0, 59)
    sekunda = randint(0, 59)

    czas = str(godzina) + ":" + str(minuta) + ":" + str(sekunda)
    czas2 = str(godzina) + ":" + str(minuta + 15) + ":" + str(sekunda)

    godzina = "7"
    minuta = randint(0, 40)
    sekunda = randint(0, 59)

    czas3 = godzina + ":" + str(minuta) + ":" + str(sekunda)

    value = [str(i + 17) + ".08.2020", czas, czas2, czas3]
    print(value)

    aDane.insert_row(value, 3, "USER_ENTERED")