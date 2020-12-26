import gpiozero
import datetime
import time

status = 0
b3 = gpiozero.Button(4)

while 1:
    print(b3.is_pressed)
    if b3.is_pressed and status == 0:
        status = 1
        print("[acinactive]", datetime.datetime.now().strftime("%H:%M:%S"))
    elif b3.is_pressed == 0 and status == 1:
        status = 0
        print("[ inactive ]", datetime.datetime.now().strftime("%H:%M:%S"))