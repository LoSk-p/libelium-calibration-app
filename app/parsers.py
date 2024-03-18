import typing as tp
from logger import get_logger

_LOGGER = get_logger(__name__)

class BoardData:
    def __init__(self):
        self.sensors_data: tp.Dict[int, tp.Optional[float]] = {
            1: None,
            2: None,
            3: None,
            4: None,
            5: None,
            6: None,
        }
        self.board_info: tp.Dict[str, str] = {
                "name": None,
                "serial_id": None,
                "firmware": None,
                "firmware_version": None,
                "md5_hash": None,
            }
        self.battery_level: int = 0
        self.calibration_coeffs: tp.Dict[int, tp.Dict] = {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {},
        }

class Parser:
    def __init__(self, data: str, signals: tp.List = None):
        self.signals = signals
        self.data = data

    def emit_signals(func: tp.Callable):
        def wrapper(self, *args, **kwargs):
            resp = func(self, *args, **kwargs)
            for signal in self.signals:
                signal.emit()
            return resp
        return wrapper

    @emit_signals
    def parse(self, board_data: BoardData) -> bool:
        return True

class ParserStrategy:
    def __init__(
        self,
        data_update,
        coeffs_update,
        battery_update,
        info_update,
        calibration_progress,
        restart,
    ):
        self._data_update_signal = data_update
        self._coeffs_update_signal = coeffs_update
        self._battery_update_signal = battery_update
        self._info_update_signal = info_update
        self._calibration_progress_signal = calibration_progress
        self._restart_signal = restart
        self._measure_signal = "$measure"
        self._coeffs_prefix = "#z"
        self._info_prefix = "#f"
        self._calibration_prefix = "^|"
        self._restart_prefix = "J#"

    def get_parser(self, data: str, message_id: str) -> Parser:
        _LOGGER.debug(f"Parser strategy get {data}")
        if self._restart_prefix in data:
            _LOGGER.debug("Restart parser")
            return RestartParser(data, [self._restart_signal])
        elif data.startswith(self._coeffs_prefix):
            if message_id == "w":
                return SWCoeffParser(data, [self._coeffs_update_signal])
            elif message_id == "i":
                return SWIonsCoeffParser(data, [self._coeffs_update_signal])
        elif data.startswith(self._info_prefix):
            return BoardInfoParser(data, [self._info_update_signal])
        elif data.startswith(f"${message_id}"):
            if message_id == "w":
                return SWDataParser(data, [self._data_update_signal, self._battery_update_signal])
            elif message_id == "i":
                return SWIonsDataParser(data, [self._data_update_signal, self._battery_update_signal])
        elif data.startswith(self._calibration_prefix):
            return CalibrationParser(data, [self._calibration_progress_signal])
        elif self._measure_signal in data:
            return StartMeasureParser(data)
        else:
            return TrueParser(data)
        
class RestartParser(Parser):
    @Parser.emit_signals
    def parse(self, board_data: BoardData) -> bool:
        return False

class TrueParser(Parser):
    def parse(self, board_data: BoardData) -> bool:
        return True

class StartMeasureParser(Parser):
    def parse(self, board_data: BoardData) -> bool:
        return False

class SWDataParser(Parser):
    @Parser.emit_signals
    def parse(self, board_data: BoardData) -> bool:
        _LOGGER.debug(f"Data parser got {self.data}")
        values = self.data.split("|")
        for i in range(1, 7):
            board_data.sensors_data[i] = round(float(values[i]), 3)
        board_data.battery_level = int(values[7])
        return True
    
class SWIonsDataParser(Parser):
    @Parser.emit_signals
    def parse(self, board_data: BoardData) -> bool:
        _LOGGER.debug(f"Data parser got {self.data}")
        values = self.data.split("|")
        for i in range(2, 6):
            board_data.sensors_data[i-1] = round(float(values[i]), 3)
        board_data.sensors_data[6] = round(float(values[1]), 3)
        board_data.battery_level = int(values[6])
        return True

class BoardInfoParser(Parser):
    @Parser.emit_signals
    def parse(self, board_data: BoardData) -> bool:
        _LOGGER.debug(f"Info parser got {self.data}")
        values = self.data.split("|")
        board_data.board_info["name"] = values[1]
        board_data.board_info["serial_id"] = values[2]
        board_data.board_info["firmware_version"] = values[3]
        board_data.board_info["md5_hash"] = values[4]
        board_data.board_info["firmware"] = values[5]
        return True
    
class CalibrationParser(Parser):
    def parse(self, board_data: BoardData) -> None:
        if "^|finished" in self.data:
            return True
        values = self.data[2:].split(" - ")
        self.signals[0].emit({"step": int(values[0]), "value": round(float(values[1].split("\\")[0]), 3)})
        return False

class SWCoeffParser(Parser):
    @Parser.emit_signals
    def parse(self, board_data: BoardData) -> bool:
        _LOGGER.debug(f"Coeffs parser got {self.data}")
        coeffs = []
        for value in self.data.split("|"):
            coeffs_sensor = []
            for coeff in value.split(","):
                coeffs_sensor.append(coeff)
            coeffs.append(coeffs_sensor)
        for coeff in coeffs[1]:
            board_data.calibration_coeffs[1][coeff.split("-")[0]] = round(float(coeff.split("-")[1]), 3)
        board_data.calibration_coeffs[1]["Температура"] = round(float(coeffs[4][0]), 1)
        for coeff in coeffs[2]:
            board_data.calibration_coeffs[2][coeff.split("-")[0]] = round(float(coeff.split("-")[1]), 3)
        for coeff in coeffs[3]:
            board_data.calibration_coeffs[3][coeff.split("-")[0]] = round(float(coeff.split("-")[1]), 1)
        for coeff in coeffs[5]:
            board_data.calibration_coeffs[5][coeff.split("-")[0]] = round(float(coeff.split("-")[1]), 0)
        return True
    
class SWIonsCoeffParser(Parser):
    @Parser.emit_signals
    def parse(self, board_data: BoardData) -> bool:
        _LOGGER.debug(f"Coeffs parser got {self.data}")
        coeffs = []
        for value in self.data.split("|"):
            coeffs_sensor = []
            for coeff in value.split(","):
                coeffs_sensor.append(coeff)
            coeffs.append(coeffs_sensor)
        board_data.calibration_coeffs[1] = {}
        for coeff in coeffs[1]:
            solution = f"{int(float(coeff.split('-')[0].split()[0]))} {coeff.split('-')[0].split()[1]}"
            board_data.calibration_coeffs[1][solution] = round(float(coeff.split("-")[1]), 3)
        board_data.calibration_coeffs[2] = {}
        for coeff in coeffs[2]:
            solution = f"{int(float(coeff.split('-')[0].split()[0]))} {coeff.split('-')[0].split()[1]}"
            board_data.calibration_coeffs[2][solution] = round(float(coeff.split("-")[1]), 3)
        board_data.calibration_coeffs[3] = {}
        for coeff in coeffs[3]:
            solution = f"{int(float(coeff.split('-')[0].split()[0]))} {coeff.split('-')[0].split()[1]}"
            board_data.calibration_coeffs[3][solution] = round(float(coeff.split("-")[1]), 3)
        board_data.calibration_coeffs[4] = {}
        for coeff in coeffs[4]:
            solution = f"{int(float(coeff.split('-')[0].split()[0]))} {coeff.split('-')[0].split()[1]}"
            board_data.calibration_coeffs[4][solution] = round(float(coeff.split("-")[1]), 3)
        return True