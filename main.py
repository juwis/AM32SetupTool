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

from kivy.utils import platform
if platform == 'android':
    from usb4a import usb
    from usbserial4a import serial4a
else:
    from serial.tools import list_ports
    from serial import Serial

from AM32eeprom import AM32eeprom
from AM32Connector import AM32Connector


class AM32ConftoolLayout(Widget):
    pass


class AM32ConftoolApp(App):
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

    def build(self):
        return AM32ConftoolLayout()

    def callback_button_save(self, instance):
        print("callback_button_save", self, instance.state)
        self.esc.write_eeprom(self.eeprom.get_eeprom_bytearray())

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
        device_name = instance.text

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

        self.connect_esc()

    def connect_esc(self):
        self.esc = AM32Connector(serial_port_instance=self.serial_port)
        # reload eeprom with esc config values
        self.eeprom = AM32eeprom(eeprom_bytearray=self.esc.cmd_read_eeprom())

        # no more need to connect a device, disable buttons
        self.root.ids.bl_usb_serial_devices.clear_widgets()
        self.root.ids.b_update_usb_list.disabled = True
        self.root.ids.l_usb_devices.text = "Connected to %s" % self.eeprom

        # show the config tabs
        self.create_config_tabs()
        for name in self.pages:
            tab_item = TabbedPanelItem(text=name)
            scrollview = ScrollView(size_hint=(1, None), size=(self.root_window.width, self.root_window.height))
            scrollview.add_widget(self.pages[name])
            tab_item.add_widget(scrollview)
            self.root.ids.tp_main.add_widget(tab_item)

        # and enable the save button
        self.root.ids.b_save_to_esc.disabled = False

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
    AM32ConftoolApp().run()
