import logging
import os
import re
import shlex
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path

from intelhex import IntelHex

from firmware_tools.classes import STM32, Device
from firmware_tools.utils import search_id_address


class CalledProcessError(RuntimeError):
    pass


class EepromReadFailure(Exception):
    pass


class BaseFlasher(ABC):
    def __init__(
            self,
            device: Device,
            firmware: str,
            device_id: str,
            **kwargs,
    ) -> None:
        self.cfg_folder = os.path.join(
            os.path.abspath(
                os.path.dirname(sys.argv[0]),
            ), "Config",
        )
        self.device = device
        self.firmware = firmware
        self.device_id = device_id

        self.bootloader = kwargs.get('bootloader', None)
        self.color = kwargs.get('color', None)
        self.flash_cmd = kwargs.get('flash_cmd', None)
        self.unlock_cmd = kwargs.get('unlock_cmd', None)
        self.lock_cmd = kwargs.get('lock_cmd', None)
        self.eeprom_cmd = kwargs.get('eeprom_cmd', None)
        self.erase_cmd = kwargs.get('erase_cmd', None)
        self.locker = kwargs.get('locker', None)
        self.unlocker = kwargs.get('unlocker', None)
        self.unlocked = kwargs.get('unlocked', False)
        self.eeprom_file = kwargs.get('eeprom_file', None)
        self.stm8f_folder = kwargs.get("folder_with_executable", "")
        self.tries_to_execute_cmd = kwargs.get("tries_to_execute_cmd", 1)
        self.programmer_sn = kwargs.get(
            "programmer_sn", "",
        )  # sn -- serial number

        self.files_to_remove: set[str] = set()
        self.list_dev_full_erase_eeprom = ['LQC_Wireless']

        self.stm8f_cp = (
            f'{os.path.join(self.stm8f_folder, "stm8flash")}'
            f' -c stlinkv2 -p'
        )
        logging.basicConfig(
            filemode="a+", format='%(asctime)s %(levelname)s %(message)s',
            level=logging.INFO,
        )

    @property
    def cfg_folder(self) -> str:
        return self._cfg_folder

    @cfg_folder.setter
    def cfg_folder(self, value: str) -> None:
        os.makedirs(value, exist_ok=True)
        self._cfg_folder = value

    def search_apply_device_id(self) -> None:
        self.device.id_address = self.device.id_address or search_id_address(
            self.firmware,
        )
        self.write_id_with_intelhex()

    @staticmethod
    def create_empty_ih(filepath: str, start_adr: int, end_adr: int) -> None:
        dict_intel_hex = {el: 0 for el in range(start_adr, end_adr)}
        ih_empty = IntelHex(dict_intel_hex)
        ih_empty.write_hex_file(filepath)

    def prepare_ih_file(self) -> IntelHex:
        ih = IntelHex()
        if self.device.id_address >= 0x8000:
            ih.fromfile(self.firmware, format='hex')
            return ih
        eeprom_file = os.path.join(self.cfg_folder, 'eeprom.hex')
        if self.device.name in self.list_dev_full_erase_eeprom:
            # from 4096 to 6144 - eeprom stm8l151
            self.create_empty_ih(eeprom_file, 4096, 6144)
            logging.info("Load empty eeprom")
        else:
            eeprom_read_cmd = (
                f"{self.stm8f_cp} {self.device.processor.value}"
                f" -s eeprom -r '{eeprom_file}'"
            )
            logging.info(eeprom_read_cmd)
            try:
                subprocess.run(
                    eeprom_read_cmd, shell=True,
                    capture_output=True, check=True,
                )
            except subprocess.CalledProcessError as e:
                output = e.output.decode()
                raise EepromReadFailure(
                    f"Command '{e.cmd}' returned an error"
                    f" (code {e.returncode}): {output}",
                )
            ih.fromfile(eeprom_file, format='hex')

        self.files_to_remove.add(eeprom_file)
        self.eeprom_file = eeprom_file
        return ih

    def write_id_with_intelhex(self) -> None:
        ih = self.prepare_ih_file()
        id_len = len(self.device_id) // 2
        order = -1 if isinstance(self.device.processor, STM32) else 1
        for i, byte in enumerate(re.findall('..', self.device_id)[::order]):
            ih[self.device.id_address + i] = int(byte, 16)
        if id_len == 3:
            ih[self.device.id_address + id_len] = 0x00
        if self.device.hardware_type is not None:
            ih[self.device.id_address + 4] = self.device.hardware_type
        if self.device.subtype is not None:
            if self.device.subtype_address is not None:
                ih[self.device.subtype_address] = self.device.subtype
            else:
                ih[
                    self.device.id_address +
                    self.device.subtype_offset
                ] = self.device.subtype
        if self.color is not None:
            if self.color not in self.device.possible_colors:
                logging.error(
                    f'Color must be one of {self.device.possible_colors}',
                )
            color = self.color
            ih[self.device.id_address + self.device.subtype_offset + 1] = color
        if self.eeprom_file is None:
            self.firmware = Path(self.firmware).with_stem('firmware_to_flash')
            self.files_to_remove |= {self.firmware}
            ih.write_hex_file(self.firmware)
        else:
            self.eeprom_file = Path(
                self.eeprom_file,
            ).with_stem('eeprom_to_flash')
            self.files_to_remove |= {self.eeprom_file}
            ih.write_hex_file(self.eeprom_file)

    def execute_cmd(self, cmd: str) -> bool:
        logging.info(cmd)
        for attempt in range(self.tries_to_execute_cmd):
            try:
                subprocess.check_output(
                    shlex.split(
                        cmd,
                    ), stderr=subprocess.STDOUT, timeout=30,
                )
                return True
            except subprocess.CalledProcessError as e:
                output = e.output.decode()
                if (
                        self.device.processor == STM32.STM32_L0
                        and "Info : Unable to match requested speed 300 kHz,"
                            " using 240 kHz" in output.split("\n")[-3]
                ):
                    return True
                elif attempt < self.tries_to_execute_cmd - 1:
                    logging.error(
                        f"Command {e.cmd!r} was unuccessful"
                        f" (code {e.returncode}): {output}",
                    )
                else:
                    raise CalledProcessError(
                        f"Command '{e.cmd}' returned an error"
                        f" (code {e.returncode}): {output}",
                    )
        return True

    def safe_execute(self, cmd: str, raise_error: bool = False) -> bool:
        try:
            return self.execute_cmd(cmd)
        except subprocess.CalledProcessError as e:
            [logging.info(line) for line in e.stderr.decode().split('\n')]
            if raise_error:
                raise
        return False

    @abstractmethod
    def setup_firmware_flashing(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def flash_firmware(self) -> bool:
        raise NotImplementedError

    def run(self) -> bool:
        try:
            self.setup_firmware_flashing()
            return self.flash_firmware()
        except (CalledProcessError, subprocess.TimeoutExpired) as e:
            logging.error(f'Write failed: {e}')
            return False
        finally:
            for file in self.files_to_remove:
                os.remove(file)
