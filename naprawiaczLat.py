# =================================================================================
#                                NIE DZIAŁA!!
# =================================================================================

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

for i in range(aDane.row_count):
    vDane = aDane.row_values(i + 1, value_render_option = "UNFORMATTED_VALUE")
    for j in range(len(vDane)):
        print(str(vDane[j])[:4])
        if str(vDane[j])[:4] == "1899":
            print("intruzi")
    time.sleep(1)