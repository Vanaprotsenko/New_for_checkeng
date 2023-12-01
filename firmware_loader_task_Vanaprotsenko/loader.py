from __future__ import annotations

from itertools import zip_longest

from firmware_tools import Device, JLinkFlasher, STLinkFlasher
from firmware_tools.devices import INTRUSION, SMART_HOME, SIRENS, FIRE, OTHER


class Loader:
    def __init__(self) -> None:
        pass

    @staticmethod
    def show_devices_list(devices: list[Device]) -> None:
        half_length = (len(devices) + 1) // 2
        numerated = list(enumerate(devices))
        zipper = zip_longest(
            numerated[:half_length], numerated[half_length:], fillvalue=[
                None, None,
            ],
        )
        color_ending = '\033[0m'
        for (i1, dev_1), (i2, dev_2) in zipper:
            l_col_text = (
                f"{dev_1.family}{i1:3}."
                f" {dev_1.name + dev_1.add_name:50}{color_ending}"
            )
            if dev_2:
                r_col_text = (
                    f"{dev_2.family}{i2:3}."
                    f" {dev_2.name}{dev_2.add_name}{color_ending}"
                )
            else:
                r_col_text = ""
            print(f'{l_col_text}{r_col_text}')
        print()

    def get_device(self) -> Device:
        print("Choose device category:")
        
        categories = ["INTRUSION", "SMART_HOME", "SIRENS", "FIRE", "OTHER"]
        category_mapping = {str(i): device for i, device in enumerate(
            [INTRUSION, SMART_HOME, SIRENS, FIRE, OTHER], start=1)
        }
        for i, category in enumerate(categories, start=1):
            print(f"{i}. {category}")

        category_choice = input(
            "Enter the number of desired category: "
        )
         
        if category_choice in category_mapping:
            category_devices = category_mapping[category_choice]
            self.show_devices_list(category_devices)
            
            divece_choice = input(
                "Enter the number of desired device: "
            )
            try:
                selected_device = category_devices[int(divece_choice)]
                return selected_device
            except (IndexError, ValueError):
                print("Invalid device number. Please try again.")
                return self.get_device()
        else:
            print("Invalid category. Please enter a number between 1 and 5.")
            return self.get_device()

    def get_firmware(self):
        # TODO firmware file always have extencion .hex and name in format ->
        #  [device_name][version][region][subtype][id_type].hex
        #  [DoorProtect][5.5.55.5][EU][0][3B].hex example in firmware_for_test
        #  you can create you owm files for tests
        
        firmware_name = f"[{input('Enter device name: ')}][{input('Enter firmware version: ')}]" \
                    f"[{input('Enter region: ')}][{self.choose_subtype()}][{self.input_device_id()}].hex"
                    
        if self.color_to_flash():
            firmware_name += "_color"

        return firmware_name

    def input_device_id(self):
        # TODO device id can only be 3 or 4 byte, and it`s hexadecimal
        while True:
            device_id = input("Enter device ID (hexadecimal, 3 or 4 bytes): ")

            try:
                int(device_id, 16)
            except ValueError:
                print("Invalid hexadecimal format. Please try again.")
                continue
            if len(device_id) in [6, 8]:
                return device_id
            else:
                print("Invalid length. Device ID should be 3 or 4 bytes in hexadecimal format. Please try again.")

    def color_to_flash(self) -> bool:
        while True:
            flash_color = input(
                "Do you want to flash in color? (y/n): "
            ).lower()

            if flash_color == 'y':
                return True
            elif flash_color == 'n':
                return False
            else:
                print(
                    "Invalid choice. Please enter 'y' for yes or 'n' for no."
                )

    def choose_subtype(self) -> int:
        # TODO subtype only digital in range 0 - 255
        while True:
            subtype = input("Enter subtype (0 - 255): ")

            try:
                subtype_int = int(subtype)
                if 0 <= subtype_int <= 255:
                    return subtype_int
                else:
                    print(
                        "Invalid range. Subtype should be a number between 0 and 255. Please try again."
                    )
            except ValueError:
                print(
                    "Invalid input. Subtype should be a number. Please try again."
                )

    def choose_flasher(self) -> type[JLinkFlasher] | type[STLinkFlasher]:
        while True:
            flasher_type = input("Choose flasher type (JLink/STLink): ").lower()

            if flasher_type in ['jlink', 'stlink']:
                return JLinkFlasher if flasher_type == 'jlink' else STLinkFlasher
            else:
                print("Invalid choice. Please enter 'JLink' or 'STLink'.")
                