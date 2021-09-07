# Micropython AD9850 synthesizer utility
# Copyright (C) 2021  erik.brenn@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
from machine import Pin, SPI


class SignalGen:
    CRYSTAL_FREQUENCY = 125_000_000
    FACTOR = (2 ** 32) - 1

    def __init__(self, fqud_pin=4, reset_pin=5, spi_bus=1):
        self._calibration_frequency = self.CRYSTAL_FREQUENCY
        self._frequency = 1_000_000

        self._fqud = Pin(fqud_pin, Pin.OUT)
        self._reset = Pin(reset_pin, Pin.OUT)
        if spi_bus == 1:
            self._clk = Pin(14, Pin.OUT)
            self.wakeup()
            self._hspi = SPI(1, baudrate=1_000_000, bits=8, firstbit=SPI.LSB, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
        elif spi_bus == 2:
            self._clk = Pin(18, Pin.OUT)
            self.wakeup()
            self._hspi = SPI(2, baudrate=1_000_000, bits=8, firstbit=SPI.LSB, sck=Pin(18), mosi=Pin(23), miso=Pin(19))

    def pulse_pin(self, pin):
        pin.on()
        # AD9850 FQUD pulse must be at least 7ns
        time.sleep_ms(1)
        pin.off()

    def pulse_fqud(self):
        self.pulse_pin(self._fqud)

    def pulse_clk(self):
        self.pulse_pin(self._clk)

    def pulse_reset(self):
        self.pulse_pin(self._reset)

    def calibrate(self, frequency):
        self._calibration_frequency = frequency

    def run(self):
        frequency_code = self._frequency * self.FACTOR
        frequency_code = int(frequency_code / self._calibration_frequency)
        self._hspi.write(frequency_code.to_bytes(4, "little"))
        self._hspi.write(b'\x00')
        self.pulse_fqud()

    def power_down(self):
        self.pulse_fqud()
        self._hspi.write(b'\x04')
        self.pulse_fqud()

    def power_up(self):
        self.run()

    def set_frequency(self, frequency):
        self._frequency = frequency
        self.run()

    def wakeup(self):
        self.pulse_reset()
        self.pulse_clk()
        self.pulse_fqud()
