from gpiozero import Buzzer
import time

bz1 = Buzzer(25)
bz2 = Buzzer(21)

time.sleep(10)

while True:
    bz1.on()
    print("bz1")
    time.sleep(0.2)
    bz1.off()
    time.sleep(1)

    bz2.on()
    print("bz2")
    time.sleep(0.2)
    bz2.off()
    time.sleep(1)