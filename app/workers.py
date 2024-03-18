import time
import typing as tp

import serial
import serial.tools.list_ports
from PyQt5 import QtCore
from boards import Board, BoardStatus

from logger import get_logger

BAUDRATE = 115200

_LOGGER = get_logger(__name__)


class PortDetectThread(QtCore.QThread):
    interval = 1.0
    portsUpdate = QtCore.pyqtSignal([list])

    def run(self):
        """Checks list of available ports and emits signal when necessary"""
        ports = None
        while True:
            new_ports = serial.tools.list_ports.comports()
            if ports is None or [p.name for p in ports] != [p.name for p in new_ports]:
                self.portsUpdate.emit(new_ports)
            time.sleep(self.interval)
            ports = new_ports



class BoardSerial(QtCore.QThread):
    interval = 0.1
    dataUpdate = QtCore.pyqtSignal()
    coeffsUpdate = QtCore.pyqtSignal()
    batteryUpdate = QtCore.pyqtSignal()
    infoUpdate = QtCore.pyqtSignal()
    calibrationProgressUpdate = QtCore.pyqtSignal(dict)
    currentBoardUpdate = QtCore.pyqtSignal(str)
    boardStatusUpdate = QtCore.pyqtSignal(str)     
    restartSignal = QtCore.pyqtSignal()        

    def __init__(self, port: str, boards: tp.Dict[str, Board], parent=None):
        super(QtCore.QThread, self).__init__(parent)
        self._port_is_opened = True
        if "tty" in port:
            self.port: str = f"/dev/{port}"
        else:
            self.port: str = port
        self.serial: serial.Serial = serial.Serial(self.port, BAUDRATE)
        self.current_board = None
        self._commands_queue = []
        self._allowed_send_command = False
        self.boards = boards
        self._wait_response = None

    def _define_board(self, data: str) -> None:
        # Calls on first message from board
        for board_type in self.boards:
            if self.boards[board_type].check_message_id(data):
                self.current_board = self.boards[board_type]
                self.currentBoardUpdate.emit(board_type)
                self.current_board.set_signals(
                    data_update=self.dataUpdate,
                    coeffs_update=self.coeffsUpdate,
                    battery_update=self.batteryUpdate,
                    info_update=self.infoUpdate,
                    calibration_progress=self.calibrationProgressUpdate,
                    restart=self.restartSignal,
                )
                self.boardStatusUpdate.emit(BoardStatus.Connected)
                break
        else:
            return
        self._allowed_send_command = self.current_board.parser(data)
        self.update_board_info()
        self.update_calibration_coeff()

    def update_board_info(self) -> None:
        _LOGGER.debug("Update board info call")
        self._add_command_to_queue_or_send(self.current_board.get_board_info_command())

    def update_calibration_coeff(self) -> None:
        _LOGGER.debug("Update calibration coeffs call")
        self._add_command_to_queue_or_send(self.current_board.get_show_coeff_command())

    def start_calibration(self, sensor: str, solution: str, duration: int) -> QtCore.pyqtSignal:
        self._add_command_to_queue_or_send(self.current_board.get_set_counter_command(duration))
        self._add_command_to_queue_or_send(self.current_board.get_calibration_command(solution, sensor))

    def close_connection(self):
        if self._port_is_opened:
            self.serial.close()
            self.boardStatusUpdate.emit(BoardStatus.Disconnected)
            _LOGGER.info(f"Port {self.port} is closed")
            self._port_is_opened = False

    def run(self):
        while True:
            if not self._port_is_opened:
                break
            try:
                if self.serial.inWaiting() > 0:
                    new_line = str(self.serial.readline())[2:-1]
                    _LOGGER.debug(f"New serial line: {new_line}")
                    _LOGGER.debug(f"Wait response: {self._wait_response}")
                    if self._wait_response and new_line.startswith(self._wait_response):
                        self._commands_queue.pop(0)
                        self._wait_response = None
                        _LOGGER.debug(f"Commands queue after pop: {self._commands_queue}")
                    if self.current_board is not None:
                        self._allowed_send_command = self.current_board.parser(new_line)
                    else:
                        self.boardStatusUpdate.emit(BoardStatus.Connection)
                        self._allowed_send_command = self._define_board(new_line)
                    _LOGGER.debug(f"Allow send command: {self._allowed_send_command}")
                    if self._allowed_send_command and self._commands_queue:
                        self._send_command(self._commands_queue[0])
                    time.sleep(self.interval)
            except OSError:
                self.close_connection()

    def _add_command_to_queue_or_send(self, command: tuple) -> None:
        self._commands_queue.append(command)
        if self._allowed_send_command:
            self._send_command(command)
        _LOGGER.debug(f"Send command queue: {self._commands_queue}")

    def _send_command(self, command: tuple) -> None:
        self._wait_response = command[1]
        self.serial.write(command[0])
        self._allowed_send_command = False
        _LOGGER.debug(f"Command {command} was sent")
