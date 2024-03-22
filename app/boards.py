import typing as tp

from sensors import (
    ClSensor,
    ConductivitySensor,
    NH4Sensor,
    NO2Sensor,
    NO3Sensor,
    ORPSensor,
    OxxygenSensor,
    TemperatureSensor,
    pHSensor,
    TurbiditySensor,
)
from parsers import BoardData, ParserStrategy
from logger import get_logger


_LOGGER = get_logger(__name__)


class BoardStatus:
    Connected: str = "подключено"
    Disconnected: str = "не подключено"
    Connection: str = "подключение..."


class Board:
    def __init__(self, sensors):
        self._message_id: str = ""
        self._sensor_objects = sensors
        self._board_data = BoardData()
        self._parser_strategy = None
        # self._connected_sockets: tp.Dict[str, int] = {}
        self._connected_sockets: tp.Dict[int, str] = {}
        self._sensors = {}
        self._sockets = {}
        for sensor in self._sensor_objects:
            self._sensors[sensor.get_name()] = sensor

    def set_signals(
        self,
        data_update,
        coeffs_update,
        battery_update,
        info_update,
        calibration_progress,
        restart
    ) -> None:
        self._parser_strategy = ParserStrategy(
            data_update,
            coeffs_update,
            battery_update,
            info_update,
            calibration_progress,
            restart,
        )

    def parser(self, data: str) -> bool:
        return self._parser_strategy.get_parser(data, self._message_id).parse(
            self._board_data
        )
    
    def get_current_sensor_for_socket(self, socket: int) -> tp.Optional[str]:
        return self._connected_sockets.get(socket, None)
        # for sensor_name in self._connected_sockets:
        #     if self._connected_sockets[sensor_name] == socket:
        #         return sensor_name

    def update_connected_sockets(self, connected_sockets: tp.Dict):
        self._connected_sockets = connected_sockets
        _LOGGER.debug(f"Update connected sockets: {connected_sockets}")

    def get_sensors_data(self) -> tp.Dict:
        sensors_data = {}
        for socket in self._connected_sockets:
            sensors_data[self._connected_sockets[socket]] = self._board_data.sensors_data[socket]
        return sensors_data
        # sensors_data = {}
        # for sensor_name in self._connected_sockets:
        #     sensors_data[sensor_name] = self._board_data.sensors_data[
        #         self._connected_sockets[sensor_name]
        #     ]
        # return sensors_data

    def get_calibration_coeffs(self, sensor_name: str) -> tp.Dict:
        socket = self._get_socket_for_sensor_name(sensor_name)
        return self._board_data.calibration_coeffs[socket]
        # return self._board_data.calibration_coeffs[self._connected_sockets[sensor_name]]
     
    def _get_socket_for_sensor_name(self, sensor_name: str) -> int:
        for socket in self._connected_sockets:
            if self._connected_sockets[socket] == sensor_name:
                return socket

    def get_board_info(self) -> tp.Dict:
        return self._board_data.board_info

    def check_message_id(self, data: str) -> bool:
        return data.startswith(f"${self._message_id}")

    def get_show_coeff_command(self) -> (bytes, tp.Optional[str]):
        return b"z", "#z"

    def get_board_info_command(self) -> (bytes, tp.Optional[str]):
        return b"f", "#f"

    def get_set_counter_command(self, duration: int) -> (bytes, tp.Optional[str]):
        return f"t{duration}".encode(), "#t"

    def get_sensor_names(self):
        return [sensor.get_name() for sensor in self._sensor_objects]

    def get_sensor_units(self, sensor_name: str) -> str:
        return self._sensors[sensor_name].get_units()

    def get_sensor_calibration_solutions(self, sensor_name: str) -> tp.List[str]:
        return self._sensors[sensor_name].get_calibration_solutions()

    def get_calibration_command(
        self, sensor_name: str = None
    ) -> (bytes, tp.Optional[str]):
        pass

    def get_socket_sensors(self, socket: int) -> tp.List[str]:
        return self._sockets[socket]

    def get_battery_level(self) -> int:
        return self._board_data.battery_level


class SWBoard(Board):
    def __init__(self):
        super().__init__(
            [
                TemperatureSensor(),
                pHSensor(),
                ConductivitySensor(),
                OxxygenSensor(),
                ORPSensor(),
                TurbiditySensor(),
            ]
        )
        self._message_id = "w"
        self._sockets = {
            1: ["Датчик рН"],
            2: ["Датчик кислорода"],
            3: ["Датчик проводимости"],
            4: ["Датчик температуры"],
            5: ["Датчик ОВП"],
            6: ["Датчик мутности"],
        }

    def get_calibration_command(
        self, calibration_solution: str, sensor_name: str = None
    ) -> (bytes, tp.Optional[str]):
        return (
            self._sensors[sensor_name].get_calibration_command(calibration_solution),
            "#?",
        )


class SWIonsBoard(Board):
    def __init__(self):
        super().__init__(
            [
                NO2Sensor(),
                NO3Sensor(),
                NH4Sensor(),
                ClSensor(),
                TemperatureSensor(),
            ]
        )
        self._message_id = "i"
        self._socket_calibration_commands = {
            1: ["a", "b", "c"],
            2: ["k", "l", "m"],
            3: ["n", "o", "p"],
            4: ["q", "r", "s"],
        }
        self._sockets = {
            1: ["Датчик NH4", "Датчик NO3", "Датчик NO2", "Датчик Cl"],
            2: ["Датчик NO3", "Датчик NO2", "Датчик NH4", "Датчик Cl"],
            3: ["Датчик NO2", "Датчик NO3", "Датчик NH4", "Датчик Cl"],
            4: ["Датчик Cl", "Датчик NO3", "Датчик NH4", "Датчик NO2"],
            5: [],
            6: ["Датчик температуры"],
        }

    def get_calibration_command(
        self, calibration_solution: str, sensor_name: str = None
    ) -> (bytes, tp.Optional[str]):
        consentration, solution_number = self._sensors[sensor_name].get_consentration(
            calibration_solution
        )
        # socket_command = self._socket_calibration_commands[
        #     self._connected_sockets[sensor_name]
        # ][solution_number]
        socket_command = self._socket_calibration_commands[
            self._get_socket_for_sensor_name(sensor_name)
        ][solution_number]
        return f"{socket_command}{consentration}".encode(), "#?"

    def get_multiions_calibration_command(self, sensors_on_sockets) -> str:
        pass
