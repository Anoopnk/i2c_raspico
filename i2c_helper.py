import machine
import ustruct
from micropython import const


class I2C:
    DEFAULT_ADDRESS = const(0x00)

    _device = const(0x00)
    _devices = []
    led = None
    led_timer = None

    def __init__(self, *args, i2c: machine.I2C, **kwargs):
        self._i2c = i2c
        # self._devices = kwargs.pop("devices", self._i2c.scan())
        self._device = kwargs.pop("device", self.DEFAULT_ADDRESS)
        self.led = kwargs.get("led", None)

    def format_output(self):
        return "Add:{}".format(self._device)

    def read(self, *args):
        return self.format_output()

    def print(self, *args):
        try:
            print(self.read())
        except Exception as e:
            print(e)
            self.led.on()

    def reg_read(self, add, reg, nbytes=1) -> bytes:
        return self.i2c_read(self._i2c, add, reg, nbytes)

    def dev_read_hex(self, *args):
        return hex(ord(self.dev_read(*args)))

    def dev_read(self, reg, nbytes=1) -> bytes:
        return self.reg_read(self._device, reg, nbytes)

    def dev_read_int(self, reg, nbytes=1) -> int:
        return self.to_int(self.dev_read(reg, nbytes))

    def dev_write(self, reg, data):
        self.reg_write(self._device, reg, data)

    def reg_write(self, addr, reg, data):
        # raise RuntimeError("Writing to the registers is purposefully not implemented.")
        self.i2c_write(self._i2c, addr, reg, data)

    @staticmethod
    def i2c_write(i2c, addr, reg, data):
        """
        Write bytes to the specified register.
        """

        # Construct message
        msg = bytearray()
        msg.append(data)

        # Write out message to register
        i2c.writeto_mem(addr, reg, msg)

    @staticmethod
    def i2c_read(i2c, addr: int, reg: int, nbytes=1) -> bytes:
        """
        Read byte(s) from specified register. If nbytes > 1, read from consecutive
        registers.
        """

        # Check to make sure caller is asking for 1 or more bytes
        if nbytes < 1:
            return b""

        # Request data from specified register(s) over I2C
        try:
            data = i2c.readfrom_mem(addr, reg, nbytes)
        except Exception as e:
            print("DEBUG: Add {} Reg {} Bytes {}".format(hex(addr).upper(), hex(reg).upper(), nbytes))
            raise e

        return data

    @staticmethod
    def to_int(bytes_data) -> int:
        return int.from_bytes(bytes_data, "big")

    @staticmethod
    def to_signed_int(bytes_data) -> int:
        return ustruct.unpack("<b", bytes_data)[0]

    @staticmethod
    def to_signed_short(b):
        return ustruct.unpack("<h", b)[0]

    @staticmethod
    def to_unsigned_short(b):
        return ustruct.unpack("<H", b)[0]
