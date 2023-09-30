#!python3
# -*- coding: utf-8 -*-

"""
    Class for AM32 ESC Bootloader connection.
    Writes (and reads*) flash and eeprom

    Copyright Julian Wingert, 2023, Licensed under the GPL V3
"""

import time


__author__ = 'Julian Wingert'
__copyright__ = 'Copyright 2023, AM32 ESC Setup Tool'
__license__ = 'GPL V3'
__version__ = '0.1'
__maintainer__ = 'Julian Wingert'
__status__ = 'testing'


class AM32Connector:
    """
    Class for AM32 ESC Bootloader connection.
    Writes (and reads*) flash and eeprom

    *not implemented
    """

    ACK = 0x30
    ESC_TYPE_G071ESC_2KB_PAGE = 0x2b
    ESC_TYPE_G071_EEPROM_ADDRESS = 0x7e00
    ESC_TYPE_F0ESC_1KB_PAGE = 0x1f
    ESC_TYPE_F0ESC_EEPROM_ADDRESS = 0x7c00
    ESC_TYPE_F3ESC_2KB_PAGE = 0x35
    ESC_TYPE_F3ESC_EEPROM_ADDRESS = 0xF800
    ESC_SEND_RETRIES = 8
    ESC_INIT_STRING = bytearray(
        [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x0D, ord('B'), ord('L'),
            ord('H'), ord('e'), ord('l'), ord('i'), 0xF4, 0x7D
        ]
    )

    FLASH_START_ADDRESS = 4096
    CHUNK_SIZE = 128
    EEPROM_SIZE = 48

    def __init__(self, serial_port_instance=None, baudrate=19200, wait_after_write=0.025):
        self.baudrate = baudrate
        self.wait_after_write = wait_after_write
        self.serial_port = serial_port_instance     # serial_device_name of serial.Serial()

        self.last_result = None
        self.ack_received = False
        # ESC info data, type, adress and flashing behaviour
        self.esc_type = None
        self.eeprom_address = None
        self.memory_divider_required_four = None
        self._send_buffer = bytearray()
        self._flash_file_chunks = []
        self._flash_file_num_chunks = 0
        self._flash_file_name = ""
        self.chunks_written = 0

        self._init_esc()

    def _load_bin_to_chunks(self, filename):
        self._flash_file_chunks = []
        self._flash_file_num_chunks = 0
        with open(filename, mode="rb") as bin_file:
            while buf := bin_file.read(self.CHUNK_SIZE):
                self._flash_file_chunks.append(buf)
                self._flash_file_num_chunks += 1

    def write_eeprom(self, eeprom_bytearray):
        if self.esc_type is None:
            raise FileNotFoundError("No ESC connected!")

        if len(eeprom_bytearray) != self.EEPROM_SIZE:
            print("eeprom size mismatch, %s expected, %s received" % (self.EEPROM_SIZE, len(eeprom_bytearray)))
            raise ValueError(
                "eeprom size mismatch, %s expected, %s received" % (self.EEPROM_SIZE, len(eeprom_bytearray))
            )

        tries = 0
        while True:
            res = self._send_direct(eeprom_bytearray, self.eeprom_address, send_eeprom=True)
            if res == len(eeprom_bytearray):
                print("eeprom written successfully")
                return res
            else:
                print("Retrying!")

            tries += 1
            if tries > self.ESC_SEND_RETRIES:
                print("Max retries reached writing eeprom!")
                raise ConnectionError("ESC communication problem!")

    def write_firmware(self, filename):
        if self.esc_type is None:
            raise FileNotFoundError("No ESC connected!")

        # load FW file to chunks
        self._load_bin_to_chunks(filename)
        start_time = int(time.time())
        flash_address = self.FLASH_START_ADDRESS
        self.chunks_written = 0

        for buffer in self._flash_file_chunks:

            tries = 0
            while True:
                if self.memory_divider_required_four:
                    res = self._send_direct(bytearray(buffer), flash_address >> 2)
                else:
                    res = self._send_direct(bytearray(buffer), flash_address)
                if res == len(buffer):
                    break
                else:
                    print("Retrying!")

                tries += 1
                if tries > self.ESC_SEND_RETRIES:
                    raise ConnectionError("ESC communication problem!")

            flash_address += len(buffer)
            self.chunks_written += 1
            print("%03ds: %04d/%04d" % (int(time.time() - start_time), self.chunks_written, self._flash_file_num_chunks))

    def get_flash_done_percentage(self):
        if self.chunks_written == 0:
            return 0
        return int((self.chunks_written / self._flash_file_num_chunks) * 100)

    def cmd_read_eeprom(self):
        return self._read_direct(self.EEPROM_SIZE, self.eeprom_address, read_eeprom=True)

    def _receive_ack(self):
        """
        This method tries to receive an ack byte from the serial port
        Serial data is stored in class var self.last_result
        :return: True if received, False if not
        """
        self.ack_received = False
        for tries in range(50):
            time.sleep(self.wait_after_write)
            self.last_result = self.serial_port.read_all()
            # print("res: ", self.last_result)
            if len(self.last_result) > 1:
                if int(self.last_result[-1]) == 0x30:
                    # print("Command ACK")
                    self.ack_received = True
                    return True
                else:
                    self.last_result = None

        print("ERROR! Command NACK!")
        return False

    def _init_esc(self, retries=5):
        # send init string to ESC, resetting it
        tries = 0;
        while True:
            # send init string to reset ESC (4x "\x0" -> RESET)
            self.serial_port.write(self.ESC_INIT_STRING)

            if self._receive_ack():
                break
            else:
                tries += 1
                if tries > retries:
                    raise ConnectionError("ESC init failed!")

        # check ESC reply, if not OK clear ESC info
        if self.last_result is None:
            self.esc_type = None
            self.eeprom_address = None
            self.memory_divider_required_four = None
            return False

        # check which ESC type has answered us and set ESC info accordingly
        if self.last_result[-5] == self.ESC_TYPE_G071ESC_2KB_PAGE:
            self.esc_type = self.ESC_TYPE_G071ESC_2KB_PAGE
            self.eeprom_address = self.ESC_TYPE_G071_EEPROM_ADDRESS
            self.memory_divider_required_four = True
            return True

        if self.last_result[-5] == self.ESC_TYPE_F0ESC_1KB_PAGE:
            self.esc_type = self.ESC_TYPE_F0ESC_1KB_PAGE
            self.eeprom_address = self.ESC_TYPE_F0ESC_EEPROM_ADDRESS
            self.memory_divider_required_four = False
            return True

        if self.last_result[-5] == self.ESC_TYPE_F3ESC_2KB_PAGE:
            self.esc_type = self.ESC_TYPE_F3ESC_2KB_PAGE
            self.eeprom_address = self.ESC_TYPE_F3ESC_EEPROM_ADDRESS
            self.memory_divider_required_four = False
            return True

        return False

    @staticmethod
    def crc16(crc_buffer):
        crc16 = 0
        for xb in crc_buffer:
            for j in range(8):
                if ((xb & 0x01) ^ (crc16 & 0x0001)) != 0:
                    crc16 = crc16 >> 1
                    crc16 = crc16 ^ 0xA001
                else:
                    crc16 = crc16 >> 1
                xb = xb >> 1
        crc_high_byte = (crc16 >> 8) & 0xff
        crc_low_byte = crc16 & 0xff
        return crc_high_byte, crc_low_byte

    def _append_crc(self):
        """Appends CRC to the actual send_buffer of the class"""
        crc_high_byte, crc_low_byte = self.crc16(self._send_buffer)

        # prevent reference to preserve the original data in self._send_buffer
        # this basically creates a copy. Otherwise an object referred to by self._send_buffer
        # would get modified
        self._send_buffer = bytearray(self._send_buffer)

        self._send_buffer.append(crc_low_byte)
        self._send_buffer.append(crc_high_byte)

    def _cmd_set_address(self, address):
        self._send_buffer = bytearray()
        self._send_buffer.append(0xff)  # set address
        self._send_buffer.append(0x00)
        self._send_buffer.append(((address >> 8) & 0xff))
        self._send_buffer.append((address & 0xff))

        self._append_crc()

        self.serial_port.write(self._send_buffer)

    def _cmd_set_buffer_size(self, buffer_size):
        if buffer_size == 256:
            buffer_size = 0

        self._send_buffer = bytearray()
        self._send_buffer.append(0xfe)
        self._send_buffer.append(0x00)
        self._send_buffer.append(0x00)
        self._send_buffer.append(buffer_size)

        self._append_crc()

        self.serial_port.write(self._send_buffer)

    def _cmd_write_flash(self):

        self._send_buffer = bytearray()
        self._send_buffer.append(0x01)
        self._send_buffer.append(0x01)

        self._append_crc()

        self.serial_port.write(self._send_buffer)

    def _cmd_read_flash(self, size):

        self._send_buffer = bytearray()
        self._send_buffer.append(0x03)
        self._send_buffer.append(size)

        self._append_crc()

        self.serial_port.write(self._send_buffer)

    def _send_direct(self, send_buffer, address, send_eeprom=False):
        buffer_size = len(send_buffer)
        # print(buffer_size)

        self._cmd_set_address(address)
        if not self._receive_ack():
            return -1
        # print("set address")

        self._cmd_set_buffer_size(buffer_size)
        time.sleep(self.wait_after_write)
        self.serial_port.flushInput()
        # print("set buffer size")

        self._send_buffer = send_buffer
        self._append_crc()              # appends crc to self._send_buffer....
        self.serial_port.write(self._send_buffer)
        if send_eeprom:
            time.sleep(self.wait_after_write*2)
        if not self._receive_ack():
            return -1
        # print("sent buffer")

        self._cmd_write_flash()
        time.sleep(self.wait_after_write)

        if send_eeprom:
            time.sleep(self.wait_after_write*2)

        if not self._receive_ack():
            return -1
        # print("sent write flash")

        return buffer_size

    def _read_direct(self, buffer_size, address, read_eeprom=False):
        """

        :param buffer_size: size to read from flash / eeprom
        :param address: ...to read from
        :param read_eeprom: eeprom is slower, if set adds more waiting
        :return: data read or exception
        """
        self._cmd_set_address(address)
        if not self._receive_ack():
            return -1
        # print("set address")

        self._cmd_read_flash(buffer_size)
        time.sleep(self.wait_after_write)

        if read_eeprom:
            time.sleep(self.wait_after_write*2)

        if not self._receive_ack():
            return -1

        # buffer consists of the above command, the result, two bytes crc and the ack byte
        # what we want is the buffer size from minus three bytes (2x crc plus ack)
        read_result = self.last_result[-(buffer_size+3):-3]
        crc_result = self.last_result[-4:]

        crc_high_byte, crc_low_byte = self.crc16(read_result)

        if int(crc_result[1]) == crc_low_byte and int(crc_result[2]) == crc_high_byte:
            return read_result
        else:
            raise ConnectionError("ESC communication problem! CRC mismatch!")


