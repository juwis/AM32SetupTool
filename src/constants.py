AIR_START_EEPROM = bytearray(
    [
        0x01,      # eeprom start byte, must be 1
        0x02,      # eeprom version 0-255
        0x01,      # bootloader version 0-255
        0x01,      # firmware version major
        0x23,      # firmware version minor 50
        0x4e, 0x45, 0x4f, 0x45, 0x53, 0x43, 0x20, 0x66, 0x30, 0x35, 0x31, 0x20,       # ESC name, 12 bytes
        0x00,      # direction reversed byte 17
        0x00,      # bidectional mode 1 for on 0 for off byte 18
        0x00,      # sinusoidal startup  byte 19
        0x01,      #complementary pwm byte 20
        0x01,      #variable pwm frequency 21
        0x01,      #stuck rotor protection 22
        0x02,      # timing advance x7.5, ei 2 = 15 degrees byte 23
        0x18,      # pwm frequency mutiples of 1k..  byte 24 default 24khz 0x18
        0x64,      # startup power 50-150 percent default 100 percent 0x64 byte 25
        0x37,      # motor KV in increments of 40 default 55 = 2200kv
        0x0e,      # motor poles default 14 byte 27
        0x00,      # brake on stop default 0 byte 28
        0x00,      # anti stall protection, throttle boost at low rpm.
        0x05,      # beep volume     byte 30            range 0 to 11

        # eeprom version 0x01 and later
        0x00,      # 30 Millisecond telemetry output byte 31      0 or 1
        0x80,      #servo low value =  (value*2) + 750us byte 32
        0x80,      #servo high value = (value *2) + 1750us    byte 33
        0x80,      #servo neutral base 1374 + value Us. IE 128 = 1500 us. deafault 128 (0x80)
        0x32,      #servo dead band 0-100, applied to either side of neutral.      byte 35
        0x00,      #low voltage cuttoff                                         byte 36
        0x32,      #low voltage threshold value plus 250 /10 volts. default 50 3.0volts  byte 37
        0x00,      # rc car type reversing, brake on first aplication return to center to reverse default 0  byte 38
        0x00,      # options byte. Hall sensors if equipped  byte 39
        0x0f,      # Sine Mode Range 5-25 percent of throttle default 15   byte 40
        0x0a,      # Drag Brake Strength 1-10 , 10 being full strength, default 10   byte 41
        0x0a,      # amount of brake to use when the motor is running byte 42
        0x8d,      # temperature limit 70-140 degrees C. above 140 disables, default 141. (byte 43)
        0x66,      # current protection level (value x 2) above 100 disables, default 102 (204 degrees) (byte 44)
        0x06,      # sine mode strength 1-10 default 6 byte 45

        # eeprom version 2 or later
        0x01,      # input type selector 1)Auto 2)Dshot only 3)Servo only 4)PWM 5)Serial 6)BetaFlight Safe Arming
        0x00,      # not used
    ]
)

EEPROM_BYTE_INFO = {
    "BYTE00_start_byte": "eeprom start byte, must be 1 to enable FW startup",
    "BYTE01_eeprom_version": "eeprom version 0-255",
    "BYTE02_bootloader_version": "bootloader version 0-255",
    "BYTE03_firmware_version_major": "firmware version major number",
    "BYTE04_firmware_version_minor": "firmware version minor number",
    "BYTE05_esc_name_byte_01": "ESC name, 12 bytes",
    "BYTE06_esc_name_byte_02": "ESC name, 12 bytes",
    "BYTE07_esc_name_byte_03": "ESC name, 12 bytes",
    "BYTE08_esc_name_byte_04": "ESC name, 12 bytes",
    "BYTE09_esc_name_byte_05": "ESC name, 12 bytes",
    "BYTE10_esc_name_byte_06": "ESC name, 12 bytes",
    "BYTE11_esc_name_byte_07": "ESC name, 12 bytes",
    "BYTE12_esc_name_byte_08": "ESC name, 12 bytes",
    "BYTE13_esc_name_byte_09": "ESC name, 12 bytes",
    "BYTE14_esc_name_byte_00": "ESC name, 12 bytes",
    "BYTE15_esc_name_byte_11": "ESC name, 12 bytes",
    "BYTE16_esc_name_byte_12": "ESC name, 12 bytes",
    "BYTE17_reverse_motor": "direction reverse",
    "BYTE18_bidirectional_mode": "bidirectional mode, 1=enable 0=disable",
    "BYTE19_sinusoidal_startup": "sinusoidal startup mode, 1=enable 0=disable",
    "BYTE20_complementary_pwm": "complementary pwm, 1=enable 0=disable",
    "BYTE21_variable_pwm": "variable pwm mode, 1=enable 0=disable",
    "BYTE22_stuck_rotor_prevention": "stuck rotor prevention, 1=enable 0=disable",
    "BYTE23_timing_advance": "timing advance, 0-4, represents 0-22.5 degree, factor is 7.5",
    "BYTE24_pwm_freq": "pwm frequency mutiples of 1k..",
    "BYTE25_startup_power": "startup power 50-150 percent",
    "BYTE26_motor_kv": "motor KV in increments of 40",
    "BYTE27_motor_poles": "motor poles",
    "BYTE28_stop_brake_level": "brake on stop",
    "BYTE29_anti_stall": "anti stall protection, throttle boost at low rpm, 1=enable 0=disable",
    "BYTE30_beep_volume": "beep volume range 0 to 11",
    "BYTE31_telemetry_30ms": "30 Millisecond telemetry output, 1=enable 0=disable",
    "BYTE32_servo_low_threshold": "servo low value => (value*2) + 750 in us",
    "BYTE33_servo_high_threshold": "servo high value => (value *2) + 1750 in us",
    "BYTE34_servo_neutral": "servo neutral base 1374 + value us. IE 128 = 1500 us",
    "BYTE35_servo_dead_band": "servo dead band 0-100, applied to either side of neutral",
    "BYTE36_low_voltage_cutoff_enable": "low voltage cuttoff, 1=enable 0=disable",
    "BYTE37_low_voltage_cutoff_value": "low voltage threshold value plus 250 /10 volts. default 50",
    "BYTE38_rc_car_reverse": "rc car type reversing, brake on first aplication return to center to reverse, 1=enable 0=disable",
    "BYTE39_enable_hall_sensors": "options byte. Hall sensors if equipped, 1=enable 0=disable",
    "BYTE40_sine_mode_range": "Sine Mode Range 5-25 percent of throttle",
    "BYTE41_stop_brake_level": "Drag Brake Strength 1-10 , 10 being full strength",
    "BYTE42_running_brake_level": "amount of brake to use when the motor is running",
    "BYTE43_temperature_limit_celsius": "temperature limit 70-140 degrees C. above 140 disables",
    "BYTE44_current_limit_amps": "current protection level (value x 2) above 100 disables",
    "BYTE45_sine_mode_power": "sine mode strength 1-10",
    "BYTE46_input_mode_selector": "input type selector 1)Auto 2)Dshot only 3)Servo only 4)PWM 5)Serial 6)BetaFlight Safe Arming",
    "BYTE47_unused": "not used",
}

ESC_INIT_STRING = bytearray(
    [
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x0D, ord('B'), ord('L'),
        ord('H'), ord('e'), ord('l'), ord('i'), 0xF4, 0x7D
    ]
)
