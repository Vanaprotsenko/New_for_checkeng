from firmware_tools.BaseFlasher import BaseFlasher
from firmware_tools.JLinkFlasher import JLinkFlasher
from firmware_tools.STLinkFlasher import STLinkFlasher


class FlasherFactory:
    flashers_dict: dict[str, type[BaseFlasher]] = {
        'JLink': JLinkFlasher,
        'STlink': STLinkFlasher,
    }

    @staticmethod
    def get_flasher(flasher_device: str) -> type[BaseFlasher]:
        return FlasherFactory.flashers_dict[flasher_device]
