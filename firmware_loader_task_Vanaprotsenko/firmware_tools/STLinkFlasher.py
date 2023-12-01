import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

from intelhex import bin2hex

from firmware_tools import STM8, STM32, Device
from firmware_tools.BaseFlasher import BaseFlasher
from firmware_tools.utils import delete_line, merge_files, search_id_address


class STLinkFlasher(BaseFlasher):
    def __init__(
            self, device: Device, firmware: str, device_id: str, **kwargs,
    ) -> None:
        super().__init__(device, firmware, device_id, **kwargs)
        self.setup_config = {
            STM8: self.stm8_cfg,
            STM32: self.stm32_cfg,
        }
        self.setup_target = {
            STM8: self.target_stm8,
            STM32: self.target_stm32,
        }
        self.out_of_range_pattern = (
            r'Address [a-f,0-9]{1,6} is out of'
            r' range at line (\d+)'
        )
        self.custom_openocd_scripts_path = os.path.join(
            os.path.dirname(__file__), "openocd", "scripts",
        )
        if self.programmer_sn:
            self.stm8f_cp = (
                f'{os.path.join(self.stm8f_folder, "stm8flash")}'
                f' -c stlinkv2 -S {self.programmer_sn} -p'
            )

    def search_apply_device_id(self) -> None:
        if self.device.name == "KeyPadPlus":
            return
        self.device.id_address = self.device.id_address or search_id_address(
            self.firmware,
        )
        if isinstance(self.device.processor, STM32):
            # if firmware_tools or bootloader in .bin -> make it .hex
            if self.bootloader:
                self.bootloader = self.hex_from_bin(
                    self.bootloader, int(0x08000000),
                )
                self.firmware = self.hex_from_bin(
                    self.firmware, int(0x08020000),
                )
                self.firmware = merge_files(self.bootloader, self.firmware)
                self.files_to_remove.add(self.firmware)
            else:
                self.firmware = self.hex_from_bin(
                    self.firmware, int(0x08000000),
                )

        self.write_id_with_intelhex()

    def stm8_cfg(self) -> None:
        processor_type = self.device.processor.value.replace('?', '_')
        locker = os.path.join(
            self.cfg_folder, f'{self.device.name}_{processor_type}_lock.hex',
        )
        if not os.path.isfile(locker):
            with open(locker, 'w+') as file:
                file.write(':0148000000B7\n')
                file.write(":0148020000B5\n")
                file.write(":0148070000B0\n") if processor_type.endswith(
                    '_8',
                ) else None
                file.write(":0148080000AF\n")
                file.write(":0148090000AE\n")
                file.write(":01480A0000AD\n")
                file.write(":01480B0000AC\n")
                file.write(":01480C0000AB\n")
                file.write(":00000001FF\n")
        self.locker = self.locker or locker
        self.files_to_remove.add(locker)

    def stm32_cfg(self) -> None:
        unlocker = os.path.join(
            self.cfg_folder,
            f'{self.device.name}_{self.device.processor.value}_unlock.cfg',
        )
        locker = os.path.join(
            self.cfg_folder,
            f'{self.device.name}_{self.device.processor.value}_lock.cfg',
        )

        for o_file, operation in zip([unlocker, locker], ['unlock', 'lock']):
            if not os.path.isfile(o_file):
                with open(o_file, 'w+') as file:
                    file.write('init\n')
                    file.write("reset halt\n")
                    pattern = re.sub(
                        r'0$',
                        'x',
                        self.device.processor.value,
                    )
                    file.write(
                        f"{pattern} {operation} 0\n",
                    )
                    file.write("reset halt\n")
                    file.write("exit\n")
        self.files_to_remove |= {locker, unlocker}
        self.locker = self.locker or locker
        self.unlocker = self.unlocker or unlocker

    def target_stm8(self) -> None:
        self.unlock_cmd = f"{self.stm8f_cp} {self.device.processor.value} -u"
        self.flash_cmd = (
            f"{self.stm8f_cp} {self.device.processor.value}"
            f" -s flash -w '{self.firmware}'"
        )
        self.eeprom_cmd = (
            f"{self.stm8f_cp} {self.device.processor.value}"
            f" -s eeprom -w '{self.eeprom_file}'"
        )
        self.lock_cmd = (
            f"{self.stm8f_cp} {self.device.processor.value}"
            f" -s opt -w '{self.locker}'"
        )

    def hex_from_bin(self, file: str, offset: int) -> str:
        if file.endswith('.bin'):
            bin2hex(file, file.replace(".bin", ".hex"), offset)
            file = file.replace(".bin", ".hex")
            self.files_to_remove.add(file)
        return file

    def target_stm32(self) -> None:
        # remove '[' and ']' from filename
        if re.findall(r"\[|]", str(self.firmware)):
            fw_file_name_no_braces = re.sub(
                r"\[|]", '_', os.path.basename(self.firmware),
            )
            fw_file_name_no_braces_full_path = os.path.join(
                os.path.dirname(self.firmware), fw_file_name_no_braces,
            )
            self.firmware = shutil.copy(
                self.firmware, fw_file_name_no_braces_full_path,
            )
            self.files_to_remove |= {self.firmware}
        merge_file = os.path.abspath(self.firmware)

        interface = 'interface/stlink.cfg'
        target = f'target/{self.device.processor.value}.cfg'
        if self.device.processor == STM32.STM32_L0:
            special_config = (
                f'{self.custom_openocd_scripts_path}/'
                f'target/{self.device.processor.value}.cfg'
            )
            if Path(special_config).exists():
                target = special_config

        self.unlock_cmd = (
            f"openocd -f {interface} -f '{target}'"
            f" -f '{self.unlocker}'"
        )
        self.lock_cmd = (
            f"openocd -f {interface} -f '{target}'"
            f" -f '{self.locker}'"
        )
        self.flash_cmd = (
            f"openocd -f {interface} -f '{target}'"
            f" -c 'init' -c 'reset init'"
            f" -c 'flash write_image erase {merge_file}'"
            f" -c 'reset' -c 'shutdown'"
        )

    def flash_stm(self, raise_error: bool = True) -> bool:
        try:
            self.unlock(raise_error)
            self.flash(raise_error)
            self.write_eerprom(raise_error)
            self.lock(raise_error)
            return True
        except subprocess.CalledProcessError as e:
            [logging.info(line) for line in e.stderr.decode().split('\n')]
            if raise_error:
                raise
        return False

    def unlock(self, raise_error: bool = True) -> bool:
        if not self.unlocked:
            return self.safe_execute(self.unlock_cmd, raise_error=raise_error)
        else:
            return True

    def flash(self, raise_error: bool = True) -> bool:
        return self.safe_execute(self.flash_cmd, raise_error=raise_error)

    def write_eerprom(self, raise_error: bool = True) -> bool:
        if self.eeprom_file is not None:
            return self.safe_execute(self.eeprom_cmd, raise_error=raise_error)
        else:
            return True

    def lock(self, raise_error: bool = True) -> bool:
        return self.safe_execute(self.lock_cmd, raise_error=raise_error)

    def setup_firmware_flashing(self) -> None:
        self.search_apply_device_id()
        self.setup_config[type(self.device.processor)]()
        self.setup_target[type(self.device.processor)]()

    def flash_firmware(self) -> bool:
        try:
            return self.flash_stm()
        except subprocess.CalledProcessError as e:
            if bad_lines := re.findall(
                    self.out_of_range_pattern,
                    str(e.stderr),
            ):
                for line in bad_lines:
                    line = int(line)
                    logging.info(
                        f'Bad line {line} in firmware file, delete it',
                    )
                    delete_line(self.firmware, line)
                return self.flash_stm()
            else:
                raise
