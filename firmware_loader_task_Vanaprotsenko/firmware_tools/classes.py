from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union


class ProcessorType(Enum):
    pass


class STM8(ProcessorType):
    STM8_6 = 'stm8l151?6'
    STM8_8 = 'stm8l151?8'


class STM32(ProcessorType):
    STM32_F1X = 'stm32f1x'
    STM32_F4X = 'stm32f4x'
    STM32_L0 = 'stm32l0'
    STM32_U5 = 'stm32u5x'


class CC(ProcessorType):
    CC_1310 = 'cc1310'
    CC_1352 = 'cc1352'


class DevFamily(Enum):
    pass


class DevRadio(DevFamily):
    INTRUSION = '\033[93m'
    SIRENS = '\033[94m'
    SMART_HOME = '\033[92m'
    FIRE = '\033[91m'
    OTHER = '\033[95m'


class DevFibra(DevFamily):
    SIRENS_FIBRA = '\033[1m\033[94m'
    INTRUSION_FIBRA = '\033[1m\033[93m'
    SMART_HOME_FIBRA = '\033[1m\033[92m'
    FIRE_FIBRA = '\033[1m\033[91m'
    OTHER_FIBRA = '\033[1m\033[95m'


@dataclass
class Device:
    name: str
    processor: ProcessorType
    family: DevFamily
    add_name: str = ''
    hardware_type: Union[hex, dict[str, hex], None] = None
    id_address: Optional[hex] = None
    subtype: Optional[int] = None
    subtype_address: Optional[hex] = None
    subtype_offset: int = 4  # subtype byte offset relative to id_address

    possible_colors: tuple[int, int] = (1, 2)
