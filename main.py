from sys import stdin

import machine
import time
from SensorsPool import SensorsPool

led = machine.Pin(25, machine.Pin.OUT)
timer_led = machine.Timer()


class Timer:
    timers = []

    def add(self, **kwargs):
        self.timers.append(machine.Timer())
        self.timers[-1].init(**kwargs)

    def clear(self):
        [tm.deinit() for tm in self.timers]
        self.timers.clear()


class InfRun:
    status = True


timers = Timer()
inf_run = InfRun()


def led_toggle(*args):
    led.toggle()


def reset():
    led.off()


def c():
    machine.mem32[0x40058000] = machine.mem32[0x40058000] & ~(1 << 30)


# Init
timer_led.init(freq=60, mode=machine.Timer.PERIODIC, callback=led_toggle)
for sda_number in [4, 8]:
    SDA = machine.Pin(sda_number, mode=machine.Pin.OPEN_DRAIN, pull=machine.Pin.PULL_UP)
    SCL = machine.Pin(sda_number + 1, mode=machine.Pin.OPEN_DRAIN, pull=machine.Pin.PULL_UP)

    # Init I2C first and check for devices
    i2c = machine.I2C(0, scl=SCL, sda=SDA)
    i2c_scan = i2c.scan()
    # When no devices found, try SoftI2C for the same pins
    if not i2c_scan:
        time.sleep(1)
        # Init SoftI2C and check for devices
        i2c = machine.SoftI2C(scl=SCL, sda=SDA)
        i2c_scan = i2c.scan()
        # When no devices found for SoftI2C then try next pins
        if i2c_scan:
            break
        else:
            time.sleep(1)
    else:
        break
if not i2c_scan:
    # machine.WDT()
    timer_led.deinit()
    timer_led.init(freq=8, mode=machine.Timer.PERIODIC, callback=led_toggle)
    time.sleep(10)
    raise Exception("No I2C device found")

time.sleep(2)

timer_led.init(freq=30, mode=machine.Timer.PERIODIC, callback=led_toggle)
time.sleep(1)

timer_led.init(freq=2, mode=machine.Timer.PERIODIC, callback=led_toggle)
wdt = machine.WDT(timeout=8300)
rpi = SensorsPool(i2c=i2c, led=led, led_timer=timer_led, wdt=wdt)
time.sleep(5)
wdt.feed()
time.sleep(5)
timer_led.deinit()
wdt.feed()


def func_quit():
    inf_run.status = False
    c()
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

    acc_key = rpi.get_sensors(SensorsPool.SENSOR_DATA["Accelerometer"]["Name"])
    if acc_key:
        timers.add(freq=5, mode=machine.Timer.PERIODIC, callback=acc_key[0].print)

    bar_key = rpi.get_sensors(SensorsPool.SENSOR_DATA["Barometer"]["Name"])
    if bar_key:
        timers.add(freq=1, mode=machine.Timer.PERIODIC, callback=bar_key[0].print)

    temp_key = rpi.get_sensors(SensorsPool.SENSOR_DATA["Temperature"]["Name"])
    if temp_key:
        [timers.add(freq=1, mode=machine.Timer.PERIODIC, callback=sens.print) for sens in temp_key]


FSM_STATES = {
    "q": func_quit,
    "a": func_acc,
    "t": func_temp,
    "p": func_press,
    "z": func_all,
    "r": reset
}

try:
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
    timers.clear()
except Exception as e:
    print("Exception: {}".format(e))
finally:
    # Debugging only
    # print("Clearing WDT...")
    # c()
    pass
