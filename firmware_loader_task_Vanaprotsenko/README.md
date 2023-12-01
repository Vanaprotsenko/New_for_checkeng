# Device AQA recruitment-tasks-2023

### Project description

````
Script (and exe) for loading firmware onto devices with stm8, stm32, cc1310 processors
````

### Install project

````
- poetry install
or
- bash make.sh
````

##### - Create pull-request when you`re done
##### - You will be invited to an interview if your pull-request gets merged (remember to check comments)

## Task 1

#### Write a script (*loader.py*) to flash device firmware using the firmware_tools module.

#### The script should work through the terminal. User must provide all the necessary data(device id, sutype, etc.) for flashing.

#### Since you will not be able to flash a real device now, for successful testing you will need to mock corresponding functions that flash the processor.

## Task 2

#### Use [pytest](https://docs.pytest.org/en/7.1.x/contents.html) to write unit tests  for your code and for firmware_tools module
