import gpiozero

button1 = gpiozero.Button(17)
button2 = gpiozero.Button(22)
out = ""

while True:
    if button1.is_pressed:
        out += "1"
    else:
        out += "0"
    if button2.is_pressed:
        out += "1"
    else:
        out += "0"        
    print(out)
    out = ""
