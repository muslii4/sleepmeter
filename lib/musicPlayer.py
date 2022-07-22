import youtube_dl
import lib.configFile as configFile
import os
import random
import glob

config = configFile.getConfig()

def updateSongs():
    notDownloaded = []
    for i in config["alarmClock"]["ytList"]:
        if i.split("=")[1] + ".mp3" not in os.listdir("/home/pi/sleepmeter/songs"):
            notDownloaded.append(i)
    for i in os.listdir("/home/pi/sleepmeter/songs/"):
        if "https://www.youtube.com/watch?v=" + i.split(".")[0] not in config["alarmClock"]["ytList"]:
            os.system("rm /home/pi/sleepmeter/songs/" + i)
    for i in notDownloaded:
        video_info = youtube_dl.YoutubeDL().extract_info(url=i, download=False)
        options={
            'format': 'bestaudio/best',
            'keepvideo': False,
            'outtmpl': "/home/pi/sleepmeter/songs/" + i.split("=")[1] + f".mp3",
        }
        with youtube_dl.YoutubeDL(options) as ydl:
            try:
                ydl.download([video_info['webpage_url']])
            except youtube_dl.utils.DownloadError:
                print("could not download: ", i)
        
def killPlayer(player):
    os.system("pkill -f omxplayer")
    player.terminate()

def playRandomSong():
    path = random.choice(glob.glob("/home/pi/sleepmeter/songs/*.mp3"))
    print(path.split("/")[1])
    os.system("omxplayer " + path)
