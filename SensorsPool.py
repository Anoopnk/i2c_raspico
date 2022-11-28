import machine
import time

from AT30TSE75x import AT30TSE75x
from BME280 import BME280

Barometer = "Barometer (P:hPa, t:C, H:%rH)"
Temperature = "Temperature (T:C)"


class SensorsPool:
    TEMPERATURE_SENSOR_ADDRESS_RANGE = (0x48, 0x4F + 0x1)
    BAROMETER_SENSOR_ADDRESS_RANGE = (0X76, 0X76 + 0x1)

    _i2c = machine.I2C(0)
    _devices = []
    _sensors = {}

    def __init__(self, *args, i2c: machine.I2C, led: machine.Pin = None, **kwargs):
        self._i2c = i2c
        self._devices = self._i2c.scan()
        self._led = led
        self.print_config()

        self.spool_sensors()

    def spool_sensors(self):
        for dev in self._devices:
            if dev in range(*self.TEMPERATURE_SENSOR_ADDRESS_RANGE):
                if Temperature not in self._sensors:
                    self._sensors[Temperature] = []
                self._sensors[Temperature].append(AT30TSE75x(i2c=self._i2c, device=dev))
            elif dev in range(*self.BAROMETER_SENSOR_ADDRESS_RANGE):
                if Barometer not in self._sensors:
                    self._sensors[Barometer] = []
                self._sensors[Barometer].append(BME280(i2c=self._i2c, device=dev))
                pass

        print("Completed populating sensors pool!")

    def read(self):
        for key, devs in self._sensors.items():
            print("{}:".format(key))
            for dev in devs:
                time.sleep_ms(100)
                try:
                    print(dev.read())
                except Exception as e:
                    if self._led:
                        self._led.on()
                    print("Error on dev {} \n{}".format(dev, e))
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

