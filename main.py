from sys import stdin

import machine
import time
from SensorsPool import SensorsPool

SCL = 5
SDA = 4

led = machine.Pin(25, machine.Pin.OUT)
timer_led = machine.Timer()
wdt = machine.WDT(timeout=8300)


class Timer:
    timers = []

    def add(self, **kwargs):
        tm = machine.Timer()
        tm.init(**kwargs)

    def clear(self):
        [tm.deinit() for tm in self.timers]
        self.timers.clear()


class inf_runner:
    status = True


timers = Timer()
inf_run = inf_runner()


def led_toggle(*args):
    led.toggle()


def reset():
    led.off()


# Init
timer_led.init(freq=60, mode=machine.Timer.PERIODIC, callback=led_toggle)
i2c = machine.I2C(0, scl=machine.Pin(SCL), sda=machine.Pin(SDA))
time.sleep(2)

timer_led.init(freq=30, mode=machine.Timer.PERIODIC, callback=led_toggle)
time.sleep(1)

timer_led.init(freq=2, mode=machine.Timer.PERIODIC, callback=led_toggle)
rpi = SensorsPool(i2c=i2c, led=led, led_timer=timer_led, wdt=wdt)
time.sleep(2)
timer_led.deinit()


def func_quit():
    inf_run.status = False
    timers.clear()
    print("Bringing up python interface...")


def func_acc():
    timers.clear()
    inf_run.status = True
    acc_key = SensorsPool.SENSOR_DATA["Accelerometer"]["Name"]
    if acc_key:
        timers.add(freq=10, mode=machine.Timer.PERIODIC, callback=rpi.get_sensors(acc_key)[0].print)
    else:
        print("No Accelerometer found.")


def func_press():
    timers.clear()
    inf_run.status = True
    bar_key = SensorsPool.SENSOR_DATA["Barometer"]["Name"]
    if bar_key:
        timers.add(freq=1, mode=machine.Timer.PERIODIC, callback=rpi.get_sensors(bar_key)[0].print)
    else:
        print("No Barometer found.")


def func_temp():
    timers.clear()
    inf_run.status = True
    temp_key = SensorsPool.SENSOR_DATA["Temperature"]["Name"]
    if temp_key:
        [timers.add(freq=1, mode=machine.Timer.PERIODIC, callback=sens.print) for sens in rpi.get_sensors(temp_key)]
    else:
        print("No Temperature sensor found.")


def func_all():
    inf_run.status = True
    timers.clear()

    acc_key = SensorsPool.SENSOR_DATA["Accelerometer"]["Name"]
    if acc_key:
        timers.add(freq=5, mode=machine.Timer.PERIODIC, callback=rpi.get_sensors(acc_key)[0].print)

    bar_key = SensorsPool.SENSOR_DATA["Barometer"]["Name"]
    if bar_key:
        timers.add(freq=1, mode=machine.Timer.PERIODIC, callback=rpi.get_sensors(bar_key)[0].print)

    temp_key = SensorsPool.SENSOR_DATA["Temperature"]["Name"]
    if temp_key:
        [timers.add(freq=1, mode=machine.Timer.PERIODIC, callback=sens.print) for sens in rpi.get_sensors(temp_key)]


FSM_STATES = {
    "q": func_quit,
    "a": func_acc,
    "t": func_temp,
    "p": func_press,
    "z": func_all,
    "r": reset
}

func_all()

while inf_run.status:
    input_read = stdin.readline().strip()
    if input_read.isdigit():
        freq = int(input_read)
        print("Setting LED to {}Hz".format(freq))
        timer_led.init(freq=freq, mode=machine.Timer.PERIODIC, callback=led_toggle)
    elif input_read in FSM_STATES.keys():
        FSM_STATES[input_read]()
    time.sleep(0.05)
