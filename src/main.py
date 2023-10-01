#!python3
# -*- coding: utf-8 -*-

"""
    AM32 ESC Setup and Configuration Tool.
    Writes flash and eeprom

    Copyright Julian Wingert, 2023, Licensed under the GPL V3
"""

import os

import threading

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

    def callback_config_item_changed(self, instance, value=None):
        print("callback_config_item_changed", self, instance, value)
        for i in range(len(self.slider_list)):
            if self.slider_list[i] is instance:
                print("config_on_value: %s / %s" % (instance.value, i))
                self.eeprom[i] = int(instance.value)
                if (i == 43 or i == 44) and int(value) == self.eeprom.EEPROM_INFO[i]["max_value"]:
                    self.text_info_list[i].text = "disabled"
                else:
                    self.text_info_list[i].text = self.eeprom.scale_value(i, value).__str__()

        for i in range(len(self.checkbox_list)):
            if self.checkbox_list[i] is instance:
                print("config_on_value: %s / %s" % (instance.active, i))
                self.eeprom[i] = int(instance.active)

    def callback_button_serial_device(self, instance):
        print("callback_button_serial_device", self, instance.text)
        serial_device_name = instance.text
        self.open_serial_port(serial_device_name)
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

        # show the config tabs
        self.create_config_tabs()
        for name in self.pages:
            tab_item = TabbedPanelItem(text=name)
            scrollview = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
            scrollview.add_widget(self.pages[name])
            tab_item.add_widget(scrollview)
            self.root.ids.tp_main.add_widget(tab_item)

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
        else:
            self.serial_port = Serial(
                device_name,
                19200,
                8,
                'N',
                1,
                timeout=1
            )

    def connect_esc(self):
        self.esc = AM32Connector(serial_port_instance=self.serial_port)

    @staticmethod
    def create_configitem_layout_page():

        layout = GridLayout(cols=1, spacing=0, size_hint_y=None)
        # Make sure the height is such that there is something to scroll.
        layout.bind(minimum_height=layout.setter('height'))

        return layout

    def create_config_tabs(self):
        for byte_info in self.eeprom.get_eeprom_byte_info_list():
            if byte_info["app_page"] == "hide":
                continue

            if byte_info["app_page"] not in self.pages:
                self.pages[byte_info["app_page"]] = self.create_configitem_layout_page()

            if byte_info["type"] == "number":
                config_box = self.create_configitem_slider(
                    byte_info["byte_number"], byte_info["min_value"], byte_info["max_value"],
                    self.eeprom[byte_info["byte_number"]], byte_info["scaling_factor"],
                    byte_info["offset"], byte_info["name"].replace("_", " "),
                    self.callback_config_item_changed
                )

                self.pages[byte_info["app_page"]].add_widget(config_box)

            if byte_info["type"] == "boolean":
                config_box = self.create_configitem_checkbox(
                    byte_info["byte_number"], self.eeprom[byte_info["byte_number"]] == 1,
                    byte_info["name"].replace("_", " "), self.callback_config_item_changed
                )
                self.pages[byte_info["app_page"]].add_widget(config_box)

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

    def create_configitem_slider(self, byte_number, min_value, max_value, value, scale, offset, label_text, callback):
        # first create two boxlayouts, one vertical and an horizontal around it
        vertical_box = BoxLayout(orientation="vertical", padding=10, spacing=10, size_hint_y=None, height=200)
        horizontal_box = BoxLayout(orientation="horizontal")

        # then a label for the top-box
        new_head_label = Label(text="[b]%s:[/b]" % label_text, markup=True)

        # a textinput to show the set value
        new_value = str((value * scale) + offset)
        if (byte_number == 43 or byte_number == 44) and int(value) == self.eeprom.EEPROM_INFO[byte_number]["max_value"]:
            new_value = "disabled"
        new_text_info = TextInput(text=new_value, size_hint=(0.2, 1))

        # and the actual slider to set it
        new_slider = Slider(
            min=min_value, max=max_value, value=value, step=1,
            size_hint=(0.8, 1)
        )
        new_slider.bind(value=callback)

        # and bastel it together
        vertical_box.add_widget(new_head_label)
        vertical_box.add_widget(horizontal_box)
        horizontal_box.add_widget(new_slider)
        horizontal_box.add_widget(new_text_info)

        # append to local item list
        self.slider_list[byte_number] = new_slider
        self.text_info_list[byte_number] = new_text_info
        return vertical_box

    def create_configitem_checkbox(self, byte_number, value, label, callback):
        # first a horizontal boxlayout
        horizontal_box = BoxLayout(orientation="horizontal", padding=10, spacing=10, size_hint_y=None, height=200)

        # then a label for the top-box
        new_head_label = Label(text="[b]%s:[/b]" % label, markup=True)

        # and the checkbox
        new_checkbox = CheckBox(active=(value == 1))
        new_checkbox.bind(active=callback)
        # and bastel it together
        horizontal_box.add_widget(new_head_label)
        horizontal_box.add_widget(new_checkbox)

        # and store the checkbox in the local list
        self.checkbox_list[byte_number] = new_checkbox
        return horizontal_box


if __name__ == '__main__':
    AM32SetupToolApp().run()
