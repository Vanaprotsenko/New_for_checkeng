import pytest
from unittest.mock import patch
from firmware_tools import Device, JLinkFlasher, STLinkFlasher
from firmware_tools.classes import DevRadio
from loader import Loader


@pytest.fixture
def loader_instance():
    return Loader()


def test_get_firmware(loader_instance, capsys):
    with patch('builtins.input', side_effect=["DoorProtect", "5.5.55.5", "EU", "0", "3B", "y"]):
        with patch.object(loader_instance, 'choose_subtype', return_value="subtype_value"):
            with patch.object(loader_instance, 'input_device_id', return_value="id_type_value"):
                with patch.object(loader_instance, 'color_to_flash', return_value=True):
                    firmware_name = loader_instance.get_firmware()

    expected_name = "[DoorProtect][5.5.55.5][EU][subtype_value][id_type_value].hex_color"
    assert firmware_name == expected_name
    
    captured = capsys.readouterr()
    assert captured.out == ""


def test_get_device_valid_choice(loader_instance):
    with patch('builtins.input', side_effect=['1', '1']):
        selected_device = loader_instance.get_device()

    assert isinstance(selected_device, Device)
    assert selected_device.family == DevRadio.INTRUSION


def test_valid_input_device_id(loader_instance, capsys):
    with patch('builtins.input', side_effect=["1ABC2D3E"]):
        valid_device = loader_instance.input_device_id()
    assert valid_device == "1ABC2D3E"
    
    captured = capsys.readouterr()
    assert captured.out == ""


def test_color_to_flash_true(loader_instance):
    with patch('builtins.input', side_effect=['y']):
        flash_color = loader_instance.color_to_flash()
    assert flash_color is True
   
 
def test_color_to_flash_false(loader_instance):
    with patch('builtins.input', side_effect=['n']):
        flash_color = loader_instance.color_to_flash()      
    assert flash_color is False
        

def test_choose_subtype(loader_instance):
    with patch('builtins.input', side_effect=['3']):
        subtype = loader_instance.choose_subtype()
    assert subtype == 3


def test_choose_flasher_stlink(loader_instance):
    with patch('builtins.input', side_effect=['stlink']):
        flasher_type = loader_instance.choose_flasher()
        
    assert flasher_type == STLinkFlasher


def test_choose_flasher_jlink(loader_instance):
    with patch('builtins.input', side_effect=['jlink']):
        flasher_type_jlink = loader_instance.choose_flasher()
        
    assert flasher_type_jlink == JLinkFlasher


if __name__ == "__main__":
    pytest.main()
