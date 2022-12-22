import machine
import time

from AT30TSE75x import AT30TSE75x
from BME280 import BME280
from ADXL355 import ADXL355


class SensorsPool:

    SENSOR_DATA = {
        "Temperature": {
            "Range": (0x48, 0x4F + 0x1),
            "Name": "Temperature (T:C)",
            "Class": AT30TSE75x
        },
        "Barometer": {
            "Range": (0X76, 0X76 + 0x1),
            "Name": "Barometer (P:hPa, t:C, H:%rH)",
            "Class": BME280
        },
        "Accelerometer": {
            "Range": (0x1D, 0x1D + 0x1),
            "Name": "Accelerometer (x, y, z)",
            "Class": ADXL355
        },
    }

    _i2c = machine.I2C(0)
    _devices = []
    _sensors = {}

    def __init__(self, *args, i2c: machine.I2C, led: machine.Pin = None, **kwargs):
        self._i2c = i2c
        self._devices = self._i2c.scan()
        self._led = led
        self._led_timer = kwargs.get("led_timer", None)
        self.print_config()

        self.spool_sensors()

    def spool_sensors(self):
        for dev in self._devices:
            for sensor in self.SENSOR_DATA.values():
                if dev in range(*sensor["Range"]):
                    if sensor["Name"] not in self._sensors:
                        self._sensors[sensor["Name"]] = []
                    self._sensors[sensor["Name"]].append(sensor["Class"](i2c=self._i2c, device=dev, led=self._led))
                    break

        print("Completed populating sensors pool!")

    def read(self, key_only=None, name=False):
        for key, devs in self._sensors.items():
            if key_only is not None and key_only != key:
                continue
            if name:
                print("{}:".format(key))
            for dev in devs:
                try:
                    print(dev.read())
                except Exception as e:
                    if self._led:
                        self._led.on()
                    print("Error on dev {} - {}".format(dev, e))
            if name:
                print("-"*10)

    def timer_read(self, timer=None):
        self.read()
        self._led.off()

    def led_toggle(self, timer=None):
        self._led.toggle()

    def get_sensors(self, key: str = "") -> list:
        if key:
            return self._sensors.get(key, [])
        else:
            return sum(list(self._sensors.values()), [])

    def print_config(self):
        print("I2C Configuration: " + str(self._i2c))
        print("I2C Address      : " + ", ".join([hex(device).upper() for device in self._devices]))

