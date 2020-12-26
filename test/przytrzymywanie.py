import gpiozero
import time

status = 0
b1 = gpiozero.Button(17)

while 1:
    if b1.is_pressed and status == 0:
        status = 1
        print("[acinactive]", datetime.datetime.now().strftime("%H:%M:%S"))
    elif b1.is_pressed == 0 and status == 1:
        status = 0
        print("[ inactive ]", datetime.datetime.now().strftime("%H:%M:%S"))