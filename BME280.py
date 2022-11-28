import time
from micropython import const
from i2c_helper import I2C

BMX280_OS_SKIP = const(0)
BMX280_OS_1 = const(1)
BMX280_OS_2 = const(2)
BMX280_OS_4 = const(3)
BMX280_OS_8 = const(4)
BMX280_OS_16 = const(5)

# BMP280 Temperature Registers
BMX280_REGISTER_DIG_T1 = const(0x88)
BMX280_REGISTER_DIG_T2 = const(0x8A)
BMX280_REGISTER_DIG_T3 = const(0x8C)
# BMP280 Pressure Registers
BMX280_REGISTER_DIG_P1 = const(0x8E)
BMX280_REGISTER_DIG_P2 = const(0x90)
BMX280_REGISTER_DIG_P3 = const(0x92)
BMX280_REGISTER_DIG_P4 = const(0x94)
BMX280_REGISTER_DIG_P5 = const(0x96)
BMX280_REGISTER_DIG_P6 = const(0x98)
BMX280_REGISTER_DIG_P7 = const(0x9A)
BMX280_REGISTER_DIG_P8 = const(0x9C)
BMX280_REGISTER_DIG_P9 = const(0x9E)

BME280_REGISTER_DIG_H1 = const(0xA1)
BME280_REGISTER_DIG_H2 = const(0xE1)
BME280_REGISTER_DIG_H3 = const(0xE3)
BME280_REGISTER_DIG_H4 = const(0xE4)
BME280_REGISTER_DIG_H5 = const(0xE5)
BME280_REGISTER_DIG_H6 = const(0xE6)
BME280_REGISTER_DIG_H7 = const(0xE7)

BMX280_REGISTER_ID = const(0xD0)
BMX280_REGISTER_RESET = const(0xE0)
BMX280_REGISTER_STATUS = const(0xF3)
BMX280_REGISTER_HUMIDITY_CONTROL = const(0xF2)
BMX280_REGISTER_CONTROL = const(0xF4)
BMX280_REGISTER_CONFIG = const(0xF5)  # IIR filter config

BMX280_REGISTER_DATA = const(0xF7)

BMX280_BMP_CHIP_ID = const(0x58)  # temperature and pressure
BMX280_BME_CHIP_ID = const(0x60)  # temperature pressure and humidity


class BME280(I2C):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._chip_id = self.chip_id

        self._buf1 = bytearray(1)
        self._buf2 = bytearray(2)
        self._load_calibration()

        self._t_os = BMX280_OS_2  # temperature oversampling
        self._p_os = BMX280_OS_16  # pressure oversampling
        self._h_os = BMX280_OS_2  # pressure oversampling

        self._t_raw = 0
        self._t_fine = 0
        self._t = 0

        self._p_raw = 0
        self._p = 0

        self._h_raw = 0
        self._h = 0

        self.dev_read_wait_ms = 100
        self._new_read_ms = 200
        self._last_read_ts = 0

    @staticmethod
    def __calc_delay(sampling) -> float:
        t_delay = 0.000575 + 0.0023 * (1 << sampling)
        h_delay = 0.000575 + 0.0023 * (1 << sampling)
        p_delay = 0.001250 + 0.0023 * (1 << sampling)
        return t_delay + h_delay + p_delay

    def format_output(self):
        return "P:{} T:{} H:{}".format(*self.parse_raw())

    def _load_calibration(self):
        # read calibration data
        # < little-endian
        # H unsigned short
        # h signed short
        self._T1 = self.to_unsigned_short(self.dev_read(BMX280_REGISTER_DIG_T1, 2))
        self._T2 = self.to_signed_short(self.dev_read(BMX280_REGISTER_DIG_T2, 2))
        self._T3 = self.to_signed_short(self.dev_read(BMX280_REGISTER_DIG_T3, 2))
        self._P1 = self.to_unsigned_short(self.dev_read(BMX280_REGISTER_DIG_P1, 2))
        self._P2 = self.to_signed_short(self.dev_read(BMX280_REGISTER_DIG_P2, 2))
        self._P3 = self.to_signed_short(self.dev_read(BMX280_REGISTER_DIG_P3, 2))
        self._P4 = self.to_signed_short(self.dev_read(BMX280_REGISTER_DIG_P4, 2))
        self._P5 = self.to_signed_short(self.dev_read(BMX280_REGISTER_DIG_P5, 2))
        self._P6 = self.to_signed_short(self.dev_read(BMX280_REGISTER_DIG_P6, 2))
        self._P7 = self.to_signed_short(self.dev_read(BMX280_REGISTER_DIG_P7, 2))
        self._P8 = self.to_signed_short(self.dev_read(BMX280_REGISTER_DIG_P8, 2))
        self._P9 = self.to_signed_short(self.dev_read(BMX280_REGISTER_DIG_P9, 2))

        if self._chip_id == BMX280_BME_CHIP_ID:
            self._H1 = self.to_signed_int(self.dev_read(BME280_REGISTER_DIG_H1, 1))
            self._H2 = self.to_signed_short(self.dev_read(BME280_REGISTER_DIG_H2, 2))
            self._H3 = self.to_signed_int(self.dev_read(BME280_REGISTER_DIG_H3, 1))
            self._H6 = self.to_signed_int(self.dev_read(BME280_REGISTER_DIG_H7, 1))

            h4 = self.to_signed_int(self.dev_read(BME280_REGISTER_DIG_H4, 1))
            h4 = (h4 << 24) >> 20
            self._H4 = h4 | (
                    self.to_signed_int(self.dev_read(BME280_REGISTER_DIG_H5, 1)) & 0x0F)

            h5 = self.to_signed_int(self.dev_read(BME280_REGISTER_DIG_H6, 1))
            h5 = (h5 << 24) >> 20
            self._H5 = h5 | (
                    self.to_signed_int(self.dev_read(BME280_REGISTER_DIG_H5, 1)) >> 4 & 0x0F)

    def parse_raw(self):
        return [self.pressure/100., self.temperature, self.humidity]

    def _gauge(self):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_read_ts) > self._new_read_ms:
            self._last_read_ts = now

            if self._chip_id != BMX280_BMP_CHIP_ID:
                self.dev_write(BMX280_REGISTER_HUMIDITY_CONTROL, self._h_os)

            r = self._t_os + (self._p_os << 3) + (1 << 6)
            self.dev_write(BMX280_REGISTER_CONTROL, r)

            time.sleep_ms(100)

            if self._chip_id == BMX280_BMP_CHIP_ID:
                d = self.dev_read(BMX280_REGISTER_DATA, 6)
                self._p_raw = (d[0] << 12) + (d[1] << 4) + (d[2] >> 4)
                self._t_raw = (d[3] << 12) + (d[4] << 4) + (d[5] >> 4)
            else:
                d = self.dev_read(BMX280_REGISTER_DATA, 8)
                self._p_raw = (d[0] << 12) + (d[1] << 4) + (d[2] >> 4)
                self._t_raw = (d[3] << 12) + (d[4] << 4) + (d[5] >> 4)
                self._h_raw = (d[6] << 8) + d[7]

            self._t_fine = 0
            self._t = 0
            self._h = 0
            self._p = 0

    def _calc_t_fine(self):
        # From datasheet page 22
        self._gauge()
        if self._t_fine == 0:
            var1 = (((self._t_raw >> 3) - (self._T1 << 1)) * self._T2) >> 11
            var2 = (((((self._t_raw >> 4) - self._T1) * ((self._t_raw >> 4) - self._T1)) >> 12) * self._T3) >> 14
            self._t_fine = var1 + var2
        return self._t_fine

    @property
    def humidity(self):
        if self._chip_id == BMX280_BME_CHIP_ID and self._h == 0:
            # OLD METHOD (NON_RELATIVE)
            # var1 = self._calc_t_fine() - 76800
            # var1 = (((((self._h_raw << 14) - (self._H5 << 20) - (self._H5 * var1)) +
            #           16384) >> 15) * (((((((var1 * self._H6) >> 10) * (((var1 *
            #                                                               self._H3) >> 11) + 32768)) >> 10) + 2097152) *
            #                             self._H2 + 8192) >> 14))
            # var1 = var1 - (((((var1 >> 15) * (var1 >> 15)) >> 7) * self._H1) >> 4)
            # var1 = 0 if var1 < 0 else var1
            # var1 = 419430400 if var1 > 419430400 else var1
            # return var1 >> 12

            res = self._calc_t_fine() - 76800
            res = (self._h_raw - (self._H4 * 64.0 + self._H5 / 16384.0 * res)) * (
                        self._H2 / 65536.0 * (
                            1.0 + self._H6 / 67108864.0 * res * (1.0 + self._H3 / 67108864.0 * res)))
            res = res * (1.0 - (self._H1 * res / 524288.0))
            self._h = max(0.0, min(res, 100.0))
        else:
            print("This is a BMP not a BME, therefore it cannot measure humidity! :(")
            self._h = 0
        return self._h

    @property
    def temperature(self):
        self._calc_t_fine()
        if self._t == 0:
            self._t = ((self._t_fine * 5 + 128) >> 8) / 100.
        return self._t

    @property
    def pressure(self):
        # From datasheet page 22 (BMP) /25 (BME)
        self._calc_t_fine()
        if self._p == 0:
            var1 = self._t_fine - 128000
            var2 = var1 * var1 * self._P6
            var2 = var2 + ((var1 * self._P5) << 17)
            var2 = var2 + (self._P4 << 35)
            var1 = ((var1 * var1 * self._P3) >> 8) + ((var1 * self._P2) << 12)
            var1 = (((1 << 47) + var1) * self._P1) >> 33

            if var1 == 0:
                return 0

            p = 1048576 - self._p_raw
            p = int((((p << 31) - var2) * 3125) / var1)
            var1 = (self._P9 * (p >> 13) * (p >> 13)) >> 25
            var2 = (self._P8 * p) >> 19

            p = ((p + var1 + var2) >> 8) + (self._P7 << 4)
            self._p = p / 256.0
        return self._p

    @property
    def chip_id(self):
        chip_id = self.to_signed_int(self.dev_read(BMX280_REGISTER_ID, 1))
        return chip_id
