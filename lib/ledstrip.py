import suntime
import pytz
import time
import datetime
import serial
import lib.configFile as configFile

config = configFile.getConfig()

sun = suntime.Sun(config["led"]["lat"], config["led"]["lon"])
utc = pytz.UTC
setColor = ""
ser = serial.Serial(config["led"]["port"], 9600, timeout=1)
colors = {"highblue": config["led"]["colors"]["lowblue"], "lowblue": config["led"]["colors"]["lowblue"], "none": "000000000"}

def write(val):
    ser.write((val + "\n").encode())

def init():
    global setColor
    write("255000000")
    time.sleep(0.3)
    write("000255000")
    time.sleep(0.3)
    write("000000255")
    time.sleep(0.3)
    write("000000000")

    setColor = "000000000"

def checkColor(rl):
    global setColor
    with open(config["led"]["file"], "r+") as f:
        try:
            val = f.read().strip("\n")[-9:]
        except:
            return None
    if val != setColor:
        if val == "000000000":
            ledColor("none")
            rl.off()
        else:
            ledColor(val)
            rl.on()

def whiteTone():
    if sun.get_local_sunrise_time() < utc.localize(datetime.datetime.now()) < sun.get_local_sunset_time():
        return "255255255" # white white
    else:
        return "lowblue" # warm white

def ledColor(color):
    global setColor
    if color in colors: 
        color = colors[color]
    write(color)
    setColor = color
    with open(config["led"]["file"], "w") as f:
        f.write(color)
