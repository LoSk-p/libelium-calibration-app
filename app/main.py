import sys
import typing as tp

from PyQt5 import QtGui, QtWidgets
import pyqtgraph as pg

from boards import SWBoard, SWIonsBoard, BoardStatus
from sensors_const import MULTIIONS_SOLUTIONS, SW_BOARD_TYPE, SWIONS_BOARD_TYPE
from workers import BoardSerial, PortDetectThread
from logger import get_logger
from gui.mainwindow import Ui_MainWindow
from loading_window import LoadingWindowManager


_LOGGER = get_logger(__name__)


class Calibration:
    def __init__(self, main_window: QtWidgets.QMainWindow):
        self.main_window = main_window
        self.button = main_window.pushButtonStartCalibration
        self.progress_bar = main_window.progressBarCalibration
        self.graphics_view = main_window.graphicsViewCalibration
        self.board_serial = main_window.board_serial
        self.duration: int = (
            int(main_window.boxStabilisationTime.currentText().split()[0]) * 10 * 2
        )
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(self.duration)
        self.board_serial.calibrationProgressUpdate.connect(
            self._progress_update
        )
        self.board_serial.restartSignal.connect(self._start_calibration)
        self._start_calibration()
        self.button.setEnabled(False)

    def _start_calibration(self):
        self.main_window.loading_window_manager.show_calibration_window()
        sensor_name = self.main_window.boxSensors.currentText()
        solution = self.main_window.boxCalibrationSolution.currentText()
        self._setup_graphics()
        self.board_serial.start_calibration(sensor_name, solution, self.duration)

    def _setup_graphics(self):
        self.graphics_view.clear()
        self.pen = pg.mkPen(color=(255, 0, 0), width=3)
        self.graphics_view.setXRange(0, self.duration)
        self.line = None
        self.steps = []
        self.values = []

    def _progress_update(self, data):
        self.main_window.loading_window_manager.close_window()
        _LOGGER.debug(f"Progress update: {data['step']}")
        self.progress_bar.setValue(data["step"] + 1)
        self._draw_graphics(data)
        if data["step"] == (self.duration - 1):
            self._finish_calibration()

    def _finish_calibration(self):
        self.button.setEnabled(True)
        self.board_serial.calibrationProgressUpdate.disconnect()
        self.board_serial.restartSignal.disconnect()

    def _draw_graphics(self, data):
        self.steps.append(data["step"])
        self.values.append(data["value"])
        if self.line is None:
            self.line = self.graphics_view.plot(self.steps, self.values, pen=self.pen, symbol="o", symbolSize=5, symbolBrush="r")
        else:
            self.line.setData(self.steps, self.values)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, app=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.w = None
        self.loading_window_manager = LoadingWindowManager(self)
        self.board_serial = None
        self.board_status = BoardStatus.Disconnected
        self.current_board_type: str = SW_BOARD_TYPE
        self.boards = {SW_BOARD_TYPE: SWBoard(), SWIONS_BOARD_TYPE: SWIonsBoard()}
        self.current_board: str = self.boards[SW_BOARD_TYPE]
        self.current_sensor_calibration: str = ""
        self.port_detect: PortDetectThread = PortDetectThread()
        self.port_detect.portsUpdate.connect(self.populate_boards)
        self.port_detect.start()
        self.boxUSBPorts.currentTextChanged.connect(self.choose_port)
        self.boxSensors.currentTextChanged.connect(self.choose_sensor_calibration)
        self.radioButtonSW.toggled.connect(self.sw_swions_switched)
        self.pushButtonStartCalibration.clicked.connect(self.handle_calibration_button)
        self.progressBarCalibration.setValue(0)
        self.sensors_gui: list = [
            (
                self.comboBoxSensor_1,
                self.checkBoxSensor_1,
                self.dataMeasSensor_1,
                self.labelUnitsSensor_1,
            ),
            (
                self.comboBoxSensor_2,
                self.checkBoxSensor_2,
                self.dataMeasSensor_2,
                self.labelUnitsSensor_2,
            ),
            (
                self.comboBoxSensor_3,
                self.checkBoxSensor_3,
                self.dataMeasSensor_3,
                self.labelUnitsSensor_3,
            ),
            (
                self.comboBoxSensor_4,
                self.checkBoxSensor_4,
                self.dataMeasSensor_4,
                self.labelUnitsSensor_4,
            ),
            (
                self.comboBoxSensor_5,
                self.checkBoxSensor_5,
                self.dataMeasSensor_5,
                self.labelUnitsSensor_5,
            ),
            (
                self.comboBoxSensor_6,
                self.checkBoxSensor_6,
                self.dataMeasSensor_6,
                self.labelUnitsSensor_6,
            ),
        ]
        self.change_sensor_board(self.current_board_type)
        for sensor in self.sensors_gui:
            sensor[1].stateChanged.connect(self.sensor_enabled_changed)
            sensor[0].currentTextChanged.connect(self.sensors_sockets_changed)
        self._update_connected_sockets()
        self.sensors_enabled: tp.List[str] = []
        self.populate_sensors_on_calibration()
        self._setup_graphic()
        self.show()

    def _setup_graphic(self):
        self.graphicsViewCalibration.setBackground("w")
        self.graphicsViewCalibration.showGrid(x=True, y=True)

    def handle_calibration_button(self):
        if self.board_status == BoardStatus.Connected:
            self.calibration = Calibration(self)

    def sensors_sockets_changed(self, data):
        self._update_connected_sockets()

    def _update_connected_sockets(self):
        i = 1
        connected_sockets = {}
        for sensor in self.sensors_gui:
            connected_sockets[sensor[0].currentText()] = i
            i += 1
        self.current_board.update_connected_sockets(connected_sockets)

    def populate_sensors_on_calibration(self):
        self.sensors_enabled = []
        for checkbox in self.sensors_gui:
            if checkbox[1].checkState() and checkbox[0].currentText() != "":
                self.sensors_enabled.append(checkbox[0].currentText())
        self.boxSensors.clear()
        self.boxSensors.addItems(self.sensors_enabled)
        if self.board_status == BoardStatus.Connected:
            self._update_sensors_meas()
        if self.radioButtonSWIons.isChecked():
            self.boxSensors.addItem("Multi Ions (NO3, NH4, Cl)")

    def choose_sensor_calibration(self, sensor: str):
        self.current_sensor_calibration = sensor
        self.boxCalibrationSolution.clear()
        if sensor in self.current_board.get_sensor_names():
            self.boxCalibrationSolution.addItems(
                self.current_board.get_sensor_calibration_solutions(sensor)
            )
        else:
            self.boxCalibrationSolution.addItems(MULTIIONS_SOLUTIONS)
        if self.board_status == BoardStatus.Connected:
            self._update_calibration_coeffs()

    def sw_swions_switched(self):
        _LOGGER.debug(
            f"SW: {self.radioButtonSW.isChecked()}, SW Ions: {self.radioButtonSWIons.isChecked()}"
        )
        self.change_sensor_board(
            SW_BOARD_TYPE if self.radioButtonSW.isChecked() else SWIONS_BOARD_TYPE
        )
        self.populate_sensors_on_calibration()

    def set_sensors_units(self):
        for sensor in self.sensors_gui:
            sensor_name = sensor[0].currentText()
            if sensor_name != "":
                sensor[3].setText(self.current_board.get_sensor_units(sensor_name))
            else:
                sensor[3].setText("")

    def change_sensor_board(self, board_type: str):
        self.current_board_type = board_type
        self.current_board = self.boards[board_type]
        socket_number = 1
        for socket in self.sensors_gui:
            socket[0].clear()
            socket[0].addItems(self.current_board.get_socket_sensors(socket_number))
            if self.current_board.get_socket_sensors(socket_number) == []:
                socket[1].setEnabled(False)
            else:
                socket[1].setEnabled(True)
            socket_number += 1
        self.set_sensors_units()

    def sensor_enabled_changed(self, state: int):
        _LOGGER.debug(f"Checkbox state changed: {state}")
        self.populate_sensors_on_calibration()

    def _update_sensors_meas(self) -> None:
        sensors_data = self.current_board.get_sensors_data()
        for sensor in self.sensors_gui:
            if sensor[1].checkState():
                sensor[2].setText(str(sensors_data.get(sensor[0].currentText(), "")))
                sensor[2].setEnabled(True)
            else:
                sensor[2].setEnabled(False)
                sensor[2].setText("")

    def _update_battery(self) -> None:
        battery_data = self.current_board.get_battery_level()
        self.dataBattery.setText(str(battery_data))

    def _update_board_info(self) -> None:
        board_info = self.current_board.get_board_info()
        self.dataDeviceName.setText(board_info["name"])
        self.dataSerialID.setText(board_info["serial_id"])
        self.dataFirmware.setText(board_info["firmware"])
        self.dataFirmwareVersion.setText(board_info["firmware_version"])
        self.datamd5.setText(board_info["md5_hash"])

    def _update_calibration_coeffs(self) -> None:
        current_sensor = self.boxSensors.currentText()
        text = f"Раствор - значение\n"
        if current_sensor == "":
            self.textCalibrationValues.setText(text)
            return
        calibration_coeffs = self.current_board.get_calibration_coeffs(current_sensor)
        for value in calibration_coeffs:
            text += f"{value} - {calibration_coeffs[value]}\n"
        self.textCalibrationValues.setText(text)

    def _update_board_status(self, board_status: str):
        self.board_status = board_status
        self.dataStatus.setText(board_status)
        if self.board_status == BoardStatus.Connection:
            self.loading_window_manager.show_usb_window()
            # self.w = AnotherWindow(self)
            # self.w.show()
        else:
            self.loading_window_manager.close_window()
            # if self.w is not None:
            #     self.w.close()
            # self.w = None

    def populate_boards(self, ports: tp.List[str]):
        self.boxUSBPorts.clear()
        if self.boxUSBPorts.currentText() == "" and len(ports) > 0:
            self.boxUSBPorts.setCurrentIndex(0)
        if len(ports) > 0:
            self.boxUSBPorts.addItems([p.name for p in ports])
        else:
            sep = QtGui.QStandardItem("Платы не найдены")
            sep.setEnabled(False)
            self.boxUSBPorts.model().appendRow(sep)

    def chose_curent_board(self, board_type: str):
        self.current_board = self.boards[board_type]
        if board_type == SW_BOARD_TYPE and not self.radioButtonSW.isChecked():
            self.radioButtonSW.toggle()
        elif board_type == SWIONS_BOARD_TYPE and not self.radioButtonSWIons.isChecked():
            self.radioButtonSWIons.toggle()
        self.radioButtonSW.setEnabled(False)
        self.radioButtonSWIons.setEnabled(False)

    def choose_port(self, port):
        _LOGGER.debug(f"New port chosen: {port}")
        if port != "Платы не найдены" and port != "":
            if self.board_serial is not None:
                self.board_serial.close_connection()
            self.board_serial = BoardSerial(port, self.boards)
            self.board_serial.dataUpdate.connect(self._update_sensors_meas)
            self.board_serial.batteryUpdate.connect(self._update_battery)
            self.board_serial.infoUpdate.connect(self._update_board_info)
            self.board_serial.currentBoardUpdate.connect(self.chose_curent_board)
            self.board_serial.coeffsUpdate.connect(self._update_calibration_coeffs)
            self.board_serial.boardStatusUpdate.connect(self._update_board_status)
            self.board_serial.start()
        else:
            self.radioButtonSW.setEnabled(True)
            self.radioButtonSWIons.setEnabled(True)
    
    def moveEvent(self, event):
        self.loading_window_manager.follow_parent()

    def mousePressEvent(self, event):
        self.loading_window_manager.raise_on_top()


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
app.exec_()
