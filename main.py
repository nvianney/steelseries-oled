import ssoled as oled
import time

# oled.connect()

oled.print("Test")
time.sleep(1)
oled.print("abc")
time.sleep(1)
oled.print("n")
time.sleep(2)

counter = 3
while counter > 0:
    oled.setText(0, f"Clearing in {counter}...")
    time.sleep(1)
    counter -= 1

oled.clear()

time.sleep(2)

fullString = "SAMPLE TEXT"
counter = 0
delta = counter - len(fullString)
max_columns = 16
while delta < max_columns:
    counter += 1
    strlen = len(fullString)
    delta = counter - len(fullString)

    output = " " * max(0, delta) + fullString[len(fullString) - min(strlen, counter) : strlen]

    oled.setText(0, output)
    time.sleep(0.2)

oled.disconnect()
