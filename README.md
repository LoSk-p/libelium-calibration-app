# Libelium Calibration App

The Libelium Calibration App can be used for Libelium [Smart Water Sensors Kit](https://development.libelium.com/smart_water_sensor_guide) and [Smart Water ions Sensors kit](https://development.libelium.com/smart-water-ions-sensor-guide). App will work only with the [firmware](firmware) from this repository.

The Libelium Calibration App allows to see the current measurements and calibrate sensors.

The Libelium Calibration App is designed to be compatible with both the [Smart Water Sensors Kit](https://development.libelium.com/smart_water_sensor_guide) and the [Smart Water ions Sensors kit](https://development.libelium.com/smart-water-ions-sensor-guide) from Libelium. It is essential to note that the app is exclusively compatible with the [firmware](firmware) provided within this repository.

This application enables users to view real-time measurements and conduct sensor calibration effortlessly.

The latest executable files can be found in the latest release.

## Build from source
To build the application, Python version no older than 3.9 is required!

Clone the repo:
```bash
git clone https://github.com/Multi-Agent-io/libelium-calibration-app.git
cd libelium-calibration-app
```
Install dependencies:
```bash
pip3 install requirements.txt
```
Build GUI files:
```bash
pyuic5 app/gui/mainwindow.ui -o app/gui/mainwindow.py
```
And build executables:
```bash
pyinstaller app/main.py --onefile --windowed --name SmartWaterGUI
```
Executables will be in the `dist` folder.

## Run Python Script
```bash
pip3 install -r requirements.txt
pyuic5 app/gui/mainwindow.ui -o app/gui/mainwindow.py
python3 app/main.py
```