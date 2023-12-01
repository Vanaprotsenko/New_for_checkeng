import os

from firmware_tools import CC, STM32, Device
from firmware_tools.BaseFlasher import BaseFlasher


class JLinkFlasher(BaseFlasher):
    def __init__(
            self,
            device: Device,
            firmware: str,
            device_id: str, **kwargs,
    ) -> None:
        super().__init__(device, firmware, device_id, **kwargs)
        self.processor_config_dict = {
            CC.CC_1310: self.cc13x0_cfg,
            CC.CC_1352: self.cc13x2_cfg,
            STM32.STM32_L0: self.stm32l_cfg,
        }
        self._config_file = kwargs.get('config_file', None)

    @property
    def config_file(self) -> str:
        return self._config_file

    @config_file.setter
    def config_file(self, value: str) -> None:
        if value is not None:
            self.files_to_remove.add(value)
        self._config_file = value

    def cc13x0_cfg(self) -> str:
        processor_code = f'{self.device.processor.value.upper()}F128'
        lock_registers = ('0001FFD8', '0001FFE4', '0001FFE6')
        return self.cc_cfg(processor_code, lock_registers)

    def cc13x2_cfg(self) -> str:
        processor_code = f'{self.device.processor.value.upper()}R1F3'
        lock_registers = ('00057FE4', '00057FE8', '00057FD8')
        return self.cc_cfg(processor_code, lock_registers)

    def cc_cfg(
            self,
            processor_code: str,
            lock_registers: tuple[str, ...],
    ) -> str:
        """
        Create config file for JLink programmer device
        Command's here: https://wiki.segger.com/J-Link_Commander
        """
        flasher = os.path.join(
            self.cfg_folder, f"{self.device.processor.value}_config.jlink",
        )
        with (open(flasher, 'w') as commander_file):
            commander_file.write('SelectInterface cJTAG\n')
            commander_file.write('JTAGConf -1 -1\n')
            commander_file.write('Speed 1000\n')
            commander_file.write(f'Device {processor_code}\n')
            commander_file.write('Reset\n')
            commander_file.write('Halt\n')
            commander_file.write(f'loadfile {self.firmware}\n')
            if (
                    self.bootloader is not None
                    and self.device.id_address is not None
            ):
                commander_file.write(
                    f'loadfile {self.bootloader}'
                    f' {hex(self.device.id_address)}\n',
                )

            # Write to CCFG registers for lock mcu
            for registry in lock_registers:
                commander_file.write(f'w1 {registry} 00\n')

            commander_file.write('Exit\n')

        return flasher

    def stm32l_cfg(self) -> str:
        """
        Create config file for JLink programmer device
        Command's here: https://wiki.segger.com/J-Link_Commander
        """
        flasher = os.path.join(
            self.cfg_folder, f"{self.device.processor.value}_config.jlink",
        )
        if not os.path.isfile(flasher):
            with open(flasher, 'w') as commander_file:
                commander_file.write('SelectInterface SWD\n')
                commander_file.write('Speed 1000\n')
                commander_file.write('Device STM32L051K8 (ALLOW OPT. BYTES)\n')
                commander_file.write('r\n')  # reset
                commander_file.write('h\n')  # halt
                commander_file.write('erase\n')  # unlock
                commander_file.write(f'loadfile {self.firmware}\n')  # flash

                commander_file.write('w4 0x1FF80000 0xFF4400BB\n')
                commander_file.write('r\n')

                commander_file.write('Exit\n')

        return flasher

    def setup_firmware_flashing(self) -> None:
        self.search_apply_device_id()
        self.config_file = self.processor_config_dict[self.device.processor]()

    def flash_firmware(self) -> bool:
        serial_number_opt = ""
        if self.programmer_sn:
            serial_number_opt = f"-USB {self.programmer_sn}"

        if not self.flash_cmd:
            self.flash_cmd = (
                f'JLinkExe -ExitOnError 1'
                f' -NoGui 1 {serial_number_opt}'
                f' -CommandFile {self.config_file}'
            )
        return self.execute_cmd(self.flash_cmd)
