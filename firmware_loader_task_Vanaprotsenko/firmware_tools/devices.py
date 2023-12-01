from firmware_tools import CC, STM8, STM32, DevFibra, Device, DevRadio

INTRUSION = [
    Device('MotionCam', STM32.STM32_U5, DevRadio.INTRUSION),
    Device('DoorProtect', STM8.STM8_6, DevRadio.INTRUSION),
    Device('DoorProtectPlus', STM8.STM8_6, DevRadio.INTRUSION),
    Device('GlassProtect', STM8.STM8_6, DevRadio.INTRUSION, subtype=0),
    Device('GlassProtectS', STM8.STM8_6, DevRadio.INTRUSION, subtype=1),
]

SMART_HOME = [
    Device('KeyPad', STM8.STM8_8, DevRadio.SMART_HOME),
    Device('KeyPadCombi', CC.CC_1310, DevRadio.SMART_HOME),
    Device('Socket', STM8.STM8_6, DevRadio.SMART_HOME),
    Device('SocketTypeB', CC.CC_1310, DevRadio.SMART_HOME, subtype=5),
    Device('SocketTypeG', CC.CC_1310, DevRadio.SMART_HOME),
]

SIRENS = [
    Device('HomeSiren', STM8.STM8_6, DevRadio.SIRENS),
    Device('HomeSirenFibra', STM8.STM8_6, DevFibra.SIRENS_FIBRA),
    Device('StreetSiren', STM8.STM8_8, DevRadio.SIRENS, subtype=0),
    Device('StreetSirenFibra', STM8.STM8_8, DevFibra.SIRENS_FIBRA),
]

FIRE = [
    Device('FireProtect', STM8.STM8_6, DevRadio.FIRE),
    Device('FireProtectPlus', STM8.STM8_6, DevRadio.FIRE),
    Device('FireProtect2', CC.CC_1310, DevRadio.FIRE),
]

OTHER = [
    Device('Transmitter', STM8.STM8_6, DevRadio.OTHER),
    Device('MultiTransmitter', STM8.STM8_8, DevRadio.OTHER),
]

DEVICES = []

for family in [INTRUSION, SMART_HOME, SIRENS, FIRE, OTHER]:
    DEVICES.extend(sorted(family, key=lambda item: item.name))
