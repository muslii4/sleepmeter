from oauth2client.service_account import ServiceAccountCredentials
import gspread
import lib.configFile as configFile

config = configFile.getConfig()
scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(r"/home/pi/sleepmeter/data/apikey.json", scope)

def getSheet():
    client = gspread.authorize(credentials)
    return client.open(config["sheets"]["sheetName"]).sheet1