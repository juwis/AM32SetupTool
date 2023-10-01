#!python3
# -*- coding: utf-8 -*-

"""
    This represents the eeprom in the AM32 ESC. All bytes are documented and explained

    Copyright Julian Wingert, 2023, Licensed under the GPL V3
"""

import time


__author__ = 'Julian Wingert'
__copyright__ = 'Copyright 2023, AM32 ESC Setup Tool'
__license__ = 'GPL V3'
__version__ = '0.1'
__maintainer__ = 'Julian Wingert'
__status__ = 'testing'


class AM32eeprom:
    EEPROM_INFO = [
        {"byte_number": 0, "app_page": "hide", "name": "start_byte",
         "description": "eeprom start byte, must be 1 to enable FW startup", "type": "boolean", "min_value": 0,
         "max_value": 1, "default_value": 1, "scaling_factor": 1, "offset": 0, "label": "start byte"},
        {"byte_number": 1, "app_page": "hide", "name": "eeprom_version", "description": "eeprom version 0-255",
         "type": "number", "min_value": 0, "max_value": 255, "default_value": 2, "scaling_factor": 1, "offset": 0,
         "label": "eeprom version"},
        {"byte_number": 2, "app_page": "hide", "name": "bootloader_version", "description": "bootloader version 0-255",
         "type": "number", "min_value": 0, "max_value": 255, "default_value": 1, "scaling_factor": 1, "offset": 0,
         "label": "bootloader version"},
        {"byte_number": 3, "app_page": "hide", "name": "firmware_version_major",
         "description": "firmware version major number", "type": "number", "min_value": 0, "max_value": 255,
         "default_value": 1, "scaling_factor": 1, "offset": 0, "label": "firmware version major"},
        {"byte_number": 4, "app_page": "hide", "name": "firmware_version_minor",
         "description": "firmware version minor number", "type": "number", "min_value": 0, "max_value": 255,
         "default_value": 35, "scaling_factor": 1, "offset": 0, "label": "firmware version minor"},
        {"byte_number": 5, "app_page": "hide", "name": "esc_name_byte_01", "description": "ESC name, 12 bytes",
         "type": "character", "min_value": 0, "max_value": 1, "default_value": 78, "scaling_factor": 1, "offset": 0,
         "label": "esc name byte_01"},
        {"byte_number": 6, "app_page": "hide", "name": "esc_name_byte_02", "description": "ESC name, 12 bytes",
         "type": "character", "min_value": 0, "max_value": 1, "default_value": 69, "scaling_factor": 1, "offset": 0,
         "label": "esc name byte_02"},
        {"byte_number": 7, "app_page": "hide", "name": "esc_name_byte_03", "description": "ESC name, 12 bytes",
         "type": "character", "min_value": 0, "max_value": 1, "default_value": 79, "scaling_factor": 1, "offset": 0,
         "label": "esc name byte_03"},
        {"byte_number": 8, "app_page": "hide", "name": "esc_name_byte_04", "description": "ESC name, 12 bytes",
         "type": "character", "min_value": 0, "max_value": 1, "default_value": 69, "scaling_factor": 1, "offset": 0,
         "label": "esc name byte_04"},
        {"byte_number": 9, "app_page": "hide", "name": "esc_name_byte_05", "description": "ESC name, 12 bytes",
         "type": "character", "min_value": 0, "max_value": 1, "default_value": 83, "scaling_factor": 1, "offset": 0,
         "label": "esc name byte_05"},
        {"byte_number": 10, "app_page": "hide", "name": "esc_name_byte_06", "description": "ESC name, 12 bytes",
         "type": "character", "min_value": 0, "max_value": 1, "default_value": 67, "scaling_factor": 1, "offset": 0,
         "label": "esc name byte_06"},
        {"byte_number": 11, "app_page": "hide", "name": "esc_name_byte_07", "description": "ESC name, 12 bytes",
         "type": "character", "min_value": 0, "max_value": 1, "default_value": 32, "scaling_factor": 1, "offset": 0,
         "label": "esc name byte_07"},
        {"byte_number": 12, "app_page": "hide", "name": "esc_name_byte_08", "description": "ESC name, 12 bytes",
         "type": "character", "min_value": 0, "max_value": 1, "default_value": 102, "scaling_factor": 1, "offset": 0,
         "label": "esc name byte_08"},
        {"byte_number": 13, "app_page": "hide", "name": "esc_name_byte_09", "description": "ESC name, 12 bytes",
         "type": "character", "min_value": 0, "max_value": 1, "default_value": 48, "scaling_factor": 1, "offset": 0,
         "label": "esc name byte_09"},
        {"byte_number": 14, "app_page": "hide", "name": "esc_name_byte_00", "description": "ESC name, 12 bytes",
         "type": "character", "min_value": 0, "max_value": 1, "default_value": 53, "scaling_factor": 1, "offset": 0,
         "label": "esc name byte_00"},
        {"byte_number": 15, "app_page": "hide", "name": "esc_name_byte_11", "description": "ESC name, 12 bytes",
         "type": "character", "min_value": 0, "max_value": 1, "default_value": 49, "scaling_factor": 1, "offset": 0,
         "label": "esc name byte_11"},
        {"byte_number": 16, "app_page": "hide", "name": "esc_name_byte_12", "description": "ESC name, 12 bytes",
         "type": "character", "min_value": 0, "max_value": 1, "default_value": 32, "scaling_factor": 1, "offset": 0,
         "label": "esc name byte_12"},
        {"byte_number": 17, "app_page": "Motor", "name": "reverse_motor", "description": "direction reverse",
         "type": "boolean", "min_value": 0, "max_value": 1, "default_value": 0, "scaling_factor": 1, "offset": 0,
         "label": "reverse motor"},
        {"byte_number": 18, "app_page": "Motor", "name": "bidirectional_mode",
         "description": "bidirectional mode, 1=enable 0=disable", "type": "boolean", "min_value": 0, "max_value": 1,
         "default_value": 0, "scaling_factor": 1, "offset": 0, "label": "bidirectional mode"},
        {"byte_number": 19, "app_page": "Crawler", "name": "sinusoidal_startup",
         "description": "sinusoidal startup mode, 1=enable 0=disable", "type": "boolean", "min_value": 0,
         "max_value": 1, "default_value": 0, "scaling_factor": 1, "offset": 0, "label": "sinusoidal startup"},
        {"byte_number": 20, "app_page": "Motor", "name": "complementary_pwm",
         "description": "complementary pwm, 1=enable 0=disable", "type": "boolean", "min_value": 0, "max_value": 1,
         "default_value": 1, "scaling_factor": 1, "offset": 0, "label": "complementary pwm"},
        {"byte_number": 21, "app_page": "Motor", "name": "variable_pwm",
         "description": "variable pwm mode, 1=enable 0=disable", "type": "boolean", "min_value": 0, "max_value": 1,
         "default_value": 1, "scaling_factor": 1, "offset": 0, "label": "variable pwm"},
        {"byte_number": 22, "app_page": "Crawler", "name": "stuck_rotor_prevention",
         "description": "stuck rotor prevention, 1=enable 0=disable", "type": "boolean", "min_value": 0, "max_value": 1,
         "default_value": 0, "scaling_factor": 1, "offset": 0, "label": "stuck rotor prevention"},
        {"byte_number": 23, "app_page": "Motor", "name": "timing_advance",
         "description": "timing advance, 0-4, represents 0-22.5 degree, factor is 7.5", "type": "number",
         "min_value": 0, "max_value": 4, "default_value": 2, "scaling_factor": 7.5, "offset": 0,
         "label": "timing advance"},
        {"byte_number": 24, "app_page": "Motor", "name": "pwm_freq", "description": "pwm frequency mutiples of 1k..",
         "type": "number", "min_value": 8, "max_value": 48, "default_value": 24, "scaling_factor": 1, "offset": 0,
         "label": "pwm freq"},
        {"byte_number": 25, "app_page": "Motor", "name": "startup_power", "description": "startup power 50-150 percent",
         "type": "number", "min_value": 50, "max_value": 150, "default_value": 100, "scaling_factor": 1, "offset": 0,
         "label": "startup power"},
        {"byte_number": 26, "app_page": "Motor", "name": "motor_kv", "description": "motor KV in increments of 40",
         "type": "number", "min_value": 0, "max_value": 255, "default_value": 55, "scaling_factor": 40, "offset": 0,
         "label": "motor kv"},
        {"byte_number": 27, "app_page": "Motor", "name": "motor_poles", "description": "motor poles", "type": "number",
         "min_value": 2, "max_value": 255, "default_value": 14, "scaling_factor": 1, "offset": 0,
         "label": "motor poles"},
        {"byte_number": 28, "app_page": "Motor", "name": "stop_brake_level", "description": "brake on stop",
         "type": "number", "min_value": 0, "max_value": 10, "default_value": 0, "scaling_factor": 1, "offset": 0,
         "label": "stop brake level"},
        {"byte_number": 29, "app_page": "Crawler", "name": "anti_stall",
         "description": "anti stall protection, throttle boost at low rpm, 1=enable 0=disable", "type": "boolean",
         "min_value": 0, "max_value": 1, "default_value": 0, "scaling_factor": 1, "offset": 0, "label": "anti stall"},
        {"byte_number": 30, "app_page": "RC", "name": "beep_volume", "description": "beep volume range 0 to 11",
         "type": "number", "min_value": 0, "max_value": 11, "default_value": 5, "scaling_factor": 1, "offset": 0,
         "label": "beep volume"},
        {"byte_number": 31, "app_page": "RC", "name": "telemetry_30ms",
         "description": "30 Millisecond telemetry output, 1=enable 0=disable", "type": "boolean", "min_value": 0,
         "max_value": 1, "default_value": 0, "scaling_factor": 1, "offset": 0, "label": "telemetry 30ms"},
        {"byte_number": 32, "app_page": "RC", "name": "servo_low_threshold",
         "description": "servo low value => (value*2) + 750 in us", "type": "number", "min_value": 0, "max_value": 255,
         "default_value": 128, "scaling_factor": 2, "offset": 750, "label": "servo low threshold"},
        {"byte_number": 33, "app_page": "RC", "name": "servo_high_threshold",
         "description": "servo high value => (value *2) + 1750 in us", "type": "number", "min_value": 0,
         "max_value": 255, "default_value": 128, "scaling_factor": 2, "offset": 1750, "label": "servo high threshold"},
        {"byte_number": 34, "app_page": "RC", "name": "servo_neutral",
         "description": "servo neutral base 1374 + value us. IE 128 = 1500 us", "type": "number", "min_value": 0,
         "max_value": 255, "default_value": 128, "scaling_factor": 1, "offset": 1374, "label": "servo neutral"},
        {"byte_number": 35, "app_page": "RC", "name": "servo_dead_band",
         "description": "servo dead band 0-100, applied to either side of neutral", "type": "number", "min_value": 0,
         "max_value": 100, "default_value": 50, "scaling_factor": 1, "offset": 0, "label": "servo dead band"},
        {"byte_number": 36, "app_page": "Limits", "name": "low_voltage_cutoff_enable",
         "description": "low voltage cuttoff, 1=enable 0=disable", "type": "boolean", "min_value": 0, "max_value": 1,
         "default_value": 0, "scaling_factor": 1, "offset": 0, "label": "low voltage cutoff enable"},
        {"byte_number": 37, "app_page": "Limits", "name": "low_voltage_cutoff_value",
         "description": "low voltage threshold value plus 250 /10 volts. default 50", "type": "number", "min_value": 0,
         "max_value": 100, "default_value": 50, "scaling_factor": 1, "offset": 250,
         "label": "low voltage cutoff value"},
        {"byte_number": 38, "app_page": "Crawler", "name": "rc_car_reverse",
         "description": "rc car type reversing, brake on first aplication return to center to reverse, 1=enable 0=disable",
         "type": "boolean", "min_value": 0, "max_value": 1, "default_value": 0, "scaling_factor": 1, "offset": 0,
         "label": "rc car reverse"},
        {"byte_number": 39, "app_page": "Motor", "name": "enable_hall_sensors",
         "description": "options byte. Hall sensors if equipped, 1=enable 0=disable", "type": "boolean", "min_value": 0,
         "max_value": 1, "default_value": 0, "scaling_factor": 1, "offset": 0, "label": "enable hall sensors"},
        {"byte_number": 40, "app_page": "Crawler", "name": "sine_mode_range",
         "description": "Sine Mode Range 5-25 percent of throttle", "type": "number", "min_value": 5, "max_value": 25,
         "default_value": 15, "scaling_factor": 1, "offset": 0, "label": "sine mode range"},
        {"byte_number": 41, "app_page": "Motor", "name": "drag_brake_level",
         "description": "Drag Brake Strength 1-10 , 10 being full strength", "type": "number", "min_value": 0,
         "max_value": 10, "default_value": 10, "scaling_factor": 1, "offset": 0, "label": "stop brake level"},
        {"byte_number": 42, "app_page": "Crawler", "name": "running_brake_level",
         "description": "amount of brake to use when the motor is running", "type": "number", "min_value": 0,
         "max_value": 10, "default_value": 10, "scaling_factor": 1, "offset": 0, "label": "running brake level"},
        {"byte_number": 43, "app_page": "Limits", "name": "temperature_limit_celsius",
         "description": "temperature limit 70-140 degrees C. above 140 disables", "type": "number", "min_value": 70,
         "max_value": 141, "default_value": 141, "scaling_factor": 1, "offset": 0, "label": "temperature limit celsius"},
        {"byte_number": 44, "app_page": "Limits", "name": "current_limit_amps",
         "description": "current protection level (value x 2) above 100 disables", "type": "number", "min_value": 2,
         "max_value": 102, "default_value": 102, "scaling_factor": 1, "offset": 0, "label": "current limit amps"},
        {"byte_number": 45, "app_page": "Crawler", "name": "sine_mode_power", "description": "sine mode strength 1-10",
         "type": "number", "min_value": 0, "max_value": 1, "default_value": 6, "scaling_factor": 1, "offset": 0,
         "label": "sine mode power"},
        {"byte_number": 46, "app_page": "RC", "name": "input_mode_selector",
         "description": "input type selector 1)Auto 2)Dshot only 3)Servo only 4)PWM 5)Serial 6)BetaFlight Safe Arming",
         "type": "select", "select_options":
             {
                 1: "Auto", 2: "Dshot only", 3: "Servo only", 4: "PWM", 5: "Serial", 6: "BetaFlight Safe Arming"
             },
         "min_value": 1, "max_value": 6, "default_value": 1, "scaling_factor": 1, "offset": 0,
         "label": "input mode selector"},
        {"byte_number": 47, "app_page": "hide", "name": "unused", "description": "not used", "type": "boolean",
         "min_value": 0, "max_value": 1, "default_value": 0, "scaling_factor": 1, "offset": 0, "label": "unused"},

        {"byte_number": 512, "app_page": "hide", "name": "mppt_magic_byte", "description": "eeprom_written_mppt",
         "type": "number", "min_value": 0, "max_value": 255, "default_value": int(0x55), "scaling_factor": 1, "offset": 0, "label": "mppt_magic"},
        {"byte_number": 513, "app_page": "MPPT", "name": "enable_mppt", "description": "use mppt control",
         "type": "boolean", "min_value": 0, "max_value": 1, "default_value": 0, "scaling_factor": 1, "offset": 0, "label": "enable MPPT controller"},
        {"byte_number": 514, "app_page": "MPPT", "name": "mppt_voltage", "description": "mppt target voltage",
         "type": "number", "min_value": 0, "max_value": 255, "default_value": 0, "scaling_factor": 0.04, "offset": 5.5, "label": "MPPT voltage"},
    ]
    FULL_EEPROM_SIZE = 512+128

    def __init__(self, eeprom_bytearray=None):
        # create an empty list of correct size
        # find highest byte number:
        max_byte_number = 0
        for byte_info in self.EEPROM_INFO:
            if byte_info["byte_number"] > max_byte_number:
                max_byte_number = byte_info["byte_number"]

        self.EEPROM = [0x00] * self.FULL_EEPROM_SIZE

        if eeprom_bytearray is None:
            # default value load
            for byte_info in self.EEPROM_INFO:
                print(byte_info["byte_number"] , byte_info["default_value"])
                self.EEPROM[byte_info["byte_number"]] = byte_info["default_value"]
        else:
            self.EEPROM = [0] * len(eeprom_bytearray)
            for i in range(len(eeprom_bytearray)):
                self.EEPROM[i] = eeprom_bytearray[i]

    def get_eeprom_bytearray(self):
        return bytearray(self.EEPROM)

    def get_eeprom_byte_info_list(self):
        return self.EEPROM_INFO

    def _get_index_of_bytenumber(self, byte_number):

        for i in range(len(self.EEPROM_INFO)):
            if self.EEPROM_INFO[i]["byte_number"] == byte_number:
                return i
        return None

    def __setitem__(self, byte_number, value):
        index = self._get_index_of_bytenumber(byte_number)
        if index is None:
            raise IndexError("%s is not in EEPROM_INFO" % byte_number)

        if self.EEPROM_INFO[index]["min_value"] <= value <= self.EEPROM_INFO[index]["max_value"]:
            self.EEPROM[byte_number] = int(value)

    def scale_value(self, byte_number, value):
        index = self._get_index_of_bytenumber(byte_number)
        if index is None:
            raise IndexError("%s is not in EEPROM_INFO" % byte_number)

        return (int(value) * self.EEPROM_INFO[index]["scaling_factor"]) + self.EEPROM_INFO[index]["offset"]

    def __getitem__(self, byte_number):
        return self.EEPROM[byte_number]

    def get_byte_info(self, byte_number):
        index = self._get_index_of_bytenumber(byte_number)
        if index is None:
            raise IndexError("%s is not in EEPROM_INFO" % byte_number)
        return self.EEPROM_INFO[index]

    def __repr__(self):
        # just optics....
        esc_name = bytearray(self.EEPROM[5:16]).__str__().replace("bytearray(b", "")[:-1]
        return esc_name
