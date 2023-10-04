#!python3
# -*- coding: utf-8 -*-

"""
    AM32 ESC Setup and Configuration Tool.
    Writes flash and eeprom

    Copyright Julian Wingert, 2023, Licensed under the GPL V3
"""

import os

import threading

import serial
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock

from kivy.utils import platform
if platform == 'android':
    from usb4a import usb
    from usbserial4a import serial4a
else:
    from serial.tools import list_ports
    from serial import Serial

from AM32eeprom import AM32eeprom
from AM32Connector import AM32Connector


__author__ = 'Julian Wingert'
__copyright__ = 'Copyright 2023, AM32 ESC Setup Tool'
__license__ = 'GPL V3'
__version__ = '0.1'
__maintainer__ = 'Julian Wingert'
__status__ = 'testing'


class AM32ConftoolLayout(Widget):
    pass


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


def get_download_path():
    """Returns the default downloads path for linux or windows"""
    if os.name == 'nt':
        import winreg
        sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return location
    else:
        return os.path.join(os.path.expanduser('~'), 'downloads')


class AM32SetupToolApp(App):
    def __init__(self):
        App.__init__(self)
        self.device_name_list = []
        self.eeprom = AM32eeprom()
        self.serial_port = None
        self.esc = None
        self.slider_list = [None] * len(self.eeprom.EEPROM)
        self.text_info_list = [None] * len(self.eeprom.EEPROM)
        self.checkbox_list = [None] * len(self.eeprom.EEPROM)
        self.select_input_list = [None] * len(self.eeprom.EEPROM)
        self.pages = {}
        self.fw_file_full_path = None

    def build(self):
        return AM32ConftoolLayout()

    def callback_button_save(self, instance):
        print("callback_button_save", self, instance.state)
        try:
            self.esc.write_eeprom(self.eeprom.get_eeprom_bytearray())
        except Exception as e:
            print("Exception: %s" % str(e))

    def callback_button_update_usb_list(self, instance):
        print("callback_button_update_usb_list", self, instance.state)
        self.update_serial_devices()

    def callback_button_serial_device(self, instance):
        print("callback_button_serial_device", self, instance.text)
        serial_device_name = instance.text
        if self.open_serial_port(serial_device_name) is None:
            instance.text = "Failed!"
            instance.disabled = True
            return

        print("SERIAL open done")
        self.connect_esc()
        print("connect esc done")

        # load eeprom from esc
        eeprom_data = self.esc.cmd_read_eeprom()
        # check eeprom for correct version
        test_eeprom = AM32eeprom()
        # after connecting, update the local eeprom data with the real data from the esc
        if test_eeprom[1] == eeprom_data[1]:
            self.eeprom = AM32eeprom(eeprom_bytearray=eeprom_data)
        else:
            # eeprom version did not match
            self.write_default_eeprom()

        # no more need to connect a device, disable buttons
        self.root.ids.bl_usb_serial_devices.clear_widgets()
        self.root.ids.b_update_usb_list.disabled = True
        self.root.ids.l_usb_devices.text = "Connected to %s" % self.eeprom

        # and enable the save button and the firmware tab
        self.root.ids.b_save_to_esc.disabled = False
        self.root.ids.b_write_default_eeprom.disabled = False
        self.root.ids.tpi_firmware.disabled = False

    def write_default_eeprom(self):
        # eeprom version did not match, load default eeprom
        self.eeprom = AM32eeprom()
        # and write it
        self.esc.write_eeprom(self.eeprom.get_eeprom_bytearray())

    def callback_button_write_default_eeprom(self, instance):
        self.write_default_eeprom()

    def callback_button_fw_file(self, instance):
        self.content = LoadDialog(load=self.load_fw_file, cancel=self.dismiss_popup)
        self.content.ids.filechooser.path = get_download_path()
        self._popup = Popup(title="Load file", content=self.content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def dismiss_popup(self):
        self._popup.dismiss()

    def load_fw_file(self, path, filename):
        if len(filename) == 0:
            return

        self.fw_file_full_path = os.path.join(path, filename[0])

        if os.path.isfile(self.fw_file_full_path):
            self.root.ids.l_flash_fw_filename.text = "FLASH FROM: '%s'" % os.path.basename(filename[0])
            self.root.ids.b_flash_firmware_file.disabled = False
            self.dismiss_popup()
        else:
            self.fw_file_full_path = None

    def callback_button_flash_fw_file(self, instance):
        # disable flash button and save button to prevent threading chaos
        self.root.ids.b_flash_firmware_file.disabled = True
        self.root.ids.b_write_default_eeprom.disabled = True
        self.root.ids.b_save_to_esc.disabled = True

        threading.Thread(target=self.esc.write_firmware, args=(self.fw_file_full_path,)).start()
        Clock.schedule_interval(self.callback_update_flash_loadbar, 1)

    def callback_update_flash_loadbar(self, dt):
        percent_done = self.esc.get_flash_done_percentage()
        print(percent_done)
        self.root.ids.pb_flash_fw_file.value = percent_done
        if percent_done == 100:
            self.root.ids.l_flash_fw_filename.text = "Flash written!"
            self.root.ids.b_save_to_esc.disabled = False
            self.root.ids.b_write_default_eeprom.disabled = False
            return False
        else:
            return True

    def open_serial_port(self, serial_device_name):
        device_name = serial_device_name
        try:
            if platform == 'android':
                device = usb.get_usb_device(device_name)
                if not device:
                    self.serial_port = None
                    return

                if not usb.has_usb_permission(device):
                    usb.request_usb_permission(device)
                    return
                self.serial_port = serial4a.get_serial_port(
                    device_name,
                    19200,
                    8,
                    'N',
                    1,
                    timeout=1
                )
                return self.serial_port
            else:

                self.serial_port = Serial(
                    device_name,
                    19200,
                    8,
                    'N',
                    1,
                    timeout=1
                )
                return self.serial_port

        except serial.SerialException as e:
            print("Serial Exception", str(e))
            return None

    def connect_esc(self):
        self.esc = AM32Connector(serial_port_instance=self.serial_port)

    def update_serial_devices(self):
        self.get_serial_devices()
        self.root.ids.bl_usb_serial_devices.clear_widgets()

        if len(self.device_name_list) > 0:
            self.root.ids.l_usb_devices.text = "USB Devices found:"
        else:
            self.root.ids.l_usb_devices.text = "No USB Devices found!"

        for device_name in self.device_name_list:
            button = Button(text=device_name, on_press=self.callback_button_serial_device)
            self.root.ids.bl_usb_serial_devices.add_widget(button)

    def get_serial_devices(self):
        self.device_name_list = []
        if platform == 'android':
            usb_device_list = usb.get_usb_device_list()

            self.device_name_list = [
                device.getDeviceName() for device in usb_device_list
            ]
        else:
            usb_device_list = list_ports.comports()
            self.device_name_list = [port.device for port in usb_device_list]


if __name__ == '__main__':
    AM32SetupToolApp().run()
