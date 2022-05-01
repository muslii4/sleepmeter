import yaml

def getConfig():
    try:
        with open("/home/pi/sleepmeter/config.yaml", "r") as f:
            return yaml.load(f, Loader=yaml.FullLoader)
    except IOError:
        with open("/home/pi/sleepmeter/configExample.yaml", "r") as f:
            return yaml.load(f, Loader=yaml.FullLoader)

def getTimes1():
    config = getConfig()
    classroomTimes = config["alarmClock"]["times"]["classroom"] # 0=monday
    onlineTimes = config["alarmClock"]["times"]["online"]
    
    if config["alarmClock"]["times"]["current"] == "online":
        return onlineTimes
    elif config["alarmClock"]["times"]["current"] == "classroom":
        return classroomTimes
    else:
        return []