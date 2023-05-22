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

def init():
    global setColor
    ser.flush()
    time.sleep(1.5)

    ser.write("255000000".encode())
    time.sleep(1.3)
    ser.write("000255000".encode())
    time.sleep(1.3)
    ser.write("000000255".encode())
    time.sleep(1.3)
    ser.write("000000000".encode())

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
    ser.write(color.encode())
    setColor = color
    with open(config["led"]["file"], "w") as f:
        f.write(color)
