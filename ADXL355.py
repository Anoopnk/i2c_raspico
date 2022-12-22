import time
from micropython import const
import machine

from i2c_helper import I2C

# register addresses
REG_DEVID_AD = const(0x00)
REG_DEVID_MST = const(0x01)
REG_PARTID = const(0x02)
REG_REVID = const(0x03)
REG_STATUS = const(0x04)
REG_FIFO_ENTRIES = const(0x05)
REG_TEMP2 = const(0x06)
REG_TEMP1 = const(0x07)
REG_XDATA3 = const(0x08)
REG_XDATA2 = const(0x09)
REG_XDATA1 = const(0x0A)
REG_YDATA3 = const(0x0B)
REG_YDATA2 = const(0x0C)
REG_YDATA1 = const(0x0D)
REG_ZDATA3 = const(0x0E)
REG_ZDATA2 = const(0x0F)
REG_ZDATA1 = const(0x10)
REG_FIFO_DATA = const(0x11)
REG_OFFSET_X_H = const(0x1E)
REG_OFFSET_X_L = const(0x1F)
REG_OFFSET_Y_H = const(0x20)
REG_OFFSET_Y_L = const(0x21)
REG_OFFSET_Z_H = const(0x22)
REG_OFFSET_Z_L = const(0x23)
REG_ACT_EN = const(0x24)
REG_ACT_THRESH_H = const(0x25)
REG_ACT_THRESH_L = const(0x26)
REG_ACT_COUNT = const(0x27)
REG_FILTER = const(0x28)
REG_FIFO_SAMPLES = const(0x29)
REG_INT_MAP = const(0x2A)
REG_SYNC = const(0x2B)
REG_RANGE = const(0x2C)
REG_POWER_CTL = const(0x2D)
REG_SELF_TEST = const(0x2E)
REG_RESET = const(0x2F)

# Settings
SET_RANGE_2G = 0b01
SET_RANGE_4G = 0b10
SET_RANGE_8G = 0b11

SET_ODR_4000 = 0b0000
SET_ODR_2000 = 0b0001
SET_ODR_1000 = 0b0010
SET_ODR_500 = 0b0011
SET_ODR_250 = 0b0100
SET_ODR_125 = 0b0101
SET_ODR_62_5 = 0b0110
SET_ODR_31_25 = 0b0111
SET_ODR_15_625 = 0b1000
SET_ODR_7_813 = 0b1001
SET_ODR_3_906 = 0b1010

ODR_TO_BIT = {4000: SET_ODR_4000,
              2000: SET_ODR_2000,
              1000: SET_ODR_1000,
              500: SET_ODR_500,
              250: SET_ODR_250,
              125: SET_ODR_125,
              62.5: SET_ODR_62_5,
              31.25: SET_ODR_31_25,
              15.625: SET_ODR_15_625,
              7.813: SET_ODR_7_813,
              3.906: SET_ODR_3_906}


class ADXL355(I2C):
    factor = 2.048 * 2 / 2 ** 20

    def __init__(self, *args, i2c: machine.I2C, **kwargs):
        super().__init__(*args, i2c=i2c, **kwargs)
        self.setrange()

    def setrange(self, r=SET_RANGE_2G):
        self.stop()
        temp = self.dev_read_int(REG_RANGE)
        if r == SET_RANGE_2G:
            self.dev_write(REG_RANGE, (temp & 0b11111100) | SET_RANGE_2G)
            self.factor = 2.048 * 2 / 2 ** 20
        if r == SET_RANGE_4G:
            self.dev_write(REG_RANGE, (temp & 0b11111100) | SET_RANGE_4G)
            self.factor = 4.096 * 2 / 2 ** 20
        if r == SET_RANGE_8G:
            self.dev_write(REG_RANGE, (temp & 0b11111100) | SET_RANGE_8G)
            self.factor = 8.192 * 2 / 2 ** 20
        self.start()
        time.sleep(0.05)

    def format_output(self):
        return "X:{} Y:{} Z:{}".format(*self.get3V())

    def start(self):
        tmp = self.dev_read_int(REG_POWER_CTL)
        self.dev_write(REG_POWER_CTL, tmp & 0b0)

    def stop(self):
        tmp = self.dev_read_int(REG_POWER_CTL)
        self.dev_write(REG_POWER_CTL, tmp | 0b1)

    def temperature(self, bias=1852.0, slope=-9.05):
        temp_raw = self.dev_read(REG_TEMP2, 2)
        temp = ((temp_raw[1] & 0b00001111) << 8) | temp_raw[0]
        res = ((temp - bias) / slope) + 25
        return res

    def get3V(self):
        axis = []
        data_raw = self.dev_read(REG_XDATA3, 9)
        for datal in [data_raw[:3], data_raw[3:6], data_raw[6:]]:
            low = (datal[2] >> 4)
            mid = (datal[1] << 4)
            high = (datal[0] << 12)
            res = low | mid | high
            axis.append(float(self.twocomp(res)) * self.factor)
        return axis

    def twocomp(self, value):
        if 0x80000 & value:
            ret = - (0x0100000 - value)
        else:
            ret = value
        return ret
