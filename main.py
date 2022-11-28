from sys import stdin

import machine
import time
from SensorsPool import SensorsPool

SCL = 5
SDA = 4

led = machine.Pin(25, machine.Pin.OUT)
timer = machine.Timer()


def led_toggle(*args):
    led.toggle()


# Init
timer.init(freq=60, mode=machine.Timer.PERIODIC, callback=led_toggle)
i2c = machine.SoftI2C(scl=machine.Pin(SCL), sda=machine.Pin(SDA))
time.sleep(2)

timer.init(freq=30, mode=machine.Timer.PERIODIC, callback=led_toggle)
time.sleep(1)

timer.init(freq=2, mode=machine.Timer.PERIODIC, callback=led_toggle)
rpi = SensorsPool(i2c=i2c, led=led)
time.sleep(2)

timer.init(freq=1, mode=machine.Timer.PERIODIC, callback=rpi.timer_read)

while True:
    int_read = stdin.readline().strip()
    if int_read:
        print(int_read)
        freq = int(int_read)
        timer.init(freq=freq, mode=machine.Timer.PERIODIC, callback=led_toggle)

