import typing as tp
from logger import get_logger


_LOGGER = get_logger(__name__)


class Sensor:
    def __init__(self):
        self._name = ""
        self._units = ""
        self._calibration_solutions = []

    def get_name(self) -> str:
        return self._name

    def get_units(self) -> str:
        return self._units

    def get_calibration_solutions(self) -> tp.List[str]:
        return self._calibration_solutions

    def get_calibration_command(self, calibration_solution: str) -> tp.Optional[str]:
        return None

    def get_consentration(self, calibration_solution: str) -> (tp.Optional[str], int):
        return None


class TemperatureSensor(Sensor):
    def __init__(self):
        self._name = "Датчик температуры"
        self._units = "℃"
        self._calibration_solutions = []


class pHSensor(Sensor):
    def __init__(self):
        self._name = "Датчик рН"
        self._units = "ед. рН"
        self._calibration_solutions = ["p4", "p7", "p10"]
        self._calibration_commands = {"p4": b"r", "p7": b"q", "p10": b"p"}

    def get_calibration_command(self, calibration_solution: str) -> tp.Optional[str]:
        return self._calibration_commands.get(calibration_solution)


class ConductivitySensor(Sensor):
    def __init__(self):
        self._name = "Датчик проводимости"
        self._units = "мкСм"
        self._calibration_solutions = [
            "84 мкСм (пара 84 и 1413)",
            "1413 мкСм (пара 84 и 1413)",
            "12880 мкСм (пара 12880 и 80000)",
            "80000 мкСм (пара 12880 и 80000)",
            "12880 мкСм (пара 12880 и 150000)",
            "150000 мкСм (пара 12880 и 150000)",
        ]
        self._calibration_commands = {
            "84 мкСм (пара 84 и 1413)": b"a",
            "1413 мкСм (пара 84 и 1413)": b"k",
            "12880 мкСм (пара 12880 и 80000)": b"c",
            "80000 мкСм (пара 12880 и 80000)": b"m",
            "12880 мкСм (пара 12880 и 150000)": b"b",
            "150000 мкСм (пара 12880 и 150000)": b"l",
        }

    def get_calibration_command(self, calibration_solution: str) -> tp.Optional[str]:
        return self._calibration_commands.get(calibration_solution)


class OxxygenSensor(Sensor):
    def __init__(self):
        self._name = "Датчик кислорода"
        self._units = "%"
        self._calibration_solutions = ["0%", "100%"]
        self._calibration_commands = {"0%": b"o", "100%": b"n"}

    def get_calibration_command(self, calibration_solution: str) -> tp.Optional[str]:
        return self._calibration_commands.get(calibration_solution)


class ORPSensor(Sensor):
    def __init__(self):
        self._name = "Датчик ОВП"
        self._units = "мВ"
        self._calibration_solutions = ["225 мВ"]
        self._calibration_commands = {"225 мВ": b"s"}

    def get_calibration_command(self, calibration_solution: str) -> tp.Optional[str]:
        return self._calibration_commands.get(calibration_solution)


class TurbiditySensor(Sensor):
    def __init__(self):
        self._name = "Датчик мутности"
        self._units = "NTU"
        self._calibration_solutions = ["0 NTU", "10 NTU", "40 NTU"]
        self._calibration_commands = {"0 NTU": b"", "10 NTU": b"", "40 NTU": b""}

    def get_calibration_command(self, calibration_solution: str) -> tp.Optional[str]:
        return self._calibration_commands.get(calibration_solution)


class NO2Sensor(Sensor):
    def __init__(self):
        self._name = "Датчик NO2"
        self._units = "мг/л"
        self._calibration_solutions = ["10 мг/л", "100 мг/л", "1000 мг/л"]

    def get_consentration(self, calibration_solution: str) -> (tp.Optional[str], int):
        return (
            calibration_solution.split()[0],
            self._calibration_solutions.index(calibration_solution),
        )


class NO3Sensor(Sensor):
    def __init__(self):
        self._name = "Датчик NO3"
        self._units = "мг/л"
        self._calibration_solutions = [
            "10 мг/л",
            "100 мг/л",
            "1000 мг/л",
            "Multi-Ion 1 (132 мг/л)",
            "Multi-Ion 2 (660 мг/л)",
            "Multi-Ion 2 (1320 мг/л)",
        ]

    def get_consentration(self, calibration_solution: str) -> (tp.Optional[str], int):
        if "Multi-Ion" in calibration_solution:
            return calibration_solution.split()[2][1:], self._calibration_solutions.index(calibration_solution) - 3,
        else:
            return calibration_solution.split()[0], self._calibration_solutions.index(calibration_solution),


class NH4Sensor(Sensor):
    def __init__(self):
        self._name = "Датчик NH4"
        self._units = "мг/л"
        self._calibration_solutions = [
            "10 мг/л",
            "100 мг/л",
            "1000 мг/л",
            "Multi-Ion 1 (4 мг/л)",
            "Multi-Ion 2 (20 мг/л)",
            "Multi-Ion 2 (40 мг/л)",
        ]

    def get_consentration(self, calibration_solution: str) -> (tp.Optional[str], int):
        if "Multi-Ion" in calibration_solution:
            return calibration_solution.split()[2][1:], self._calibration_solutions.index(calibration_solution) - 3,
        else:
            return calibration_solution.split()[0], self._calibration_solutions.index(calibration_solution),


class ClSensor(Sensor):
    def __init__(self):
        self._name = "Датчик Cl"
        self._units = "мг/л"
        self._calibration_solutions = [
            "10 мг/л",
            "100 мг/л",
            "1000 мг/л",
            "Multi-Ion 1 (75 мг/л)",
            "Multi-Ion 2 (375 мг/л)",
            "Multi-Ion 2 (750 мг/л)",
        ]

    def get_consentration(self, calibration_solution: str) -> (tp.Optional[str], int):
        if "Multi-Ion" in calibration_solution:
            return calibration_solution.split()[2][1:], self._calibration_solutions.index(calibration_solution) - 3,
        else:
            return calibration_solution.split()[0], self._calibration_solutions.index(calibration_solution),
