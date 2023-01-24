from micropython import const
from i2c_helper import I2C


class AT30TSE75x(I2C):
    """
    Device addresses
     AT30TSE75 has 3 distinct subdevices with different I2C addresses:
     AT30TSE75x consist of 3 devices:
         - Temperature sensor
         - Serial EEPROM
         - Software Write Protection
     each with a separate I2C address. The 3 least significant bits
     of the 7-bit address are specified by wiring pins A2,A1,A0 to GND or VCC.


    ------

    RA - Registry address
    """
    STEP_12BIT = 0.0625

    RA_TEMPERATURE = const(0x00)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_to_12bit()

    def read_temp1(self, n_bytes=2):
        raw_temperature = self.read_temp_raw(n_bytes=n_bytes)

        if (raw_temperature & 0x8000) == 0:
            celcius_temperature = (raw_temperature >> 8) + (((raw_temperature & 0x00F0) >> 4) * self.STEP_12BIT)
        else:
            twos_complement = ~raw_temperature + 1
            celcius_temperature = - (twos_complement >> 8) - (((twos_complement & 0x00F0) >> 4) * self.STEP_12BIT)
        return celcius_temperature

    def read_temp(self, n_bytes=2):
        raw_temperature = self.read_temp_raw(n_bytes=n_bytes, return_int=False)

        temp_raw = (raw_temperature[0] << 8 | raw_temperature[1]) >> 4
        if temp_raw & 0x800:
            temp_c = (temp_raw - 0x1000) * 0.0625
        else:
            temp_c = temp_raw * 0.0625
        return temp_c

    def set_to_12bit(self):
        self.dev_write(0xAC, 0x80)

    @property
    def temp(self):
        return self.read_temp()

    def format_output(self):
        return "T:{temp} Add:{address}".format(temp=self.read_temp(), address=self._device & 0x7)

    def read_temp_raw(self, n_bytes=2, return_int=True):
        if return_int:
            return self.dev_read_int(self.RA_TEMPERATURE, n_bytes)
        else:
            return self.dev_read(self.RA_TEMPERATURE, n_bytes)
