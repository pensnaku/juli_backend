"""Environment feature exceptions"""


class EnvironmentException(Exception):
    """Base exception for environment feature"""
    pass


class WeatherException(EnvironmentException):
    """Exception for weather service errors"""
    def __init__(self, message: str, status: int = None):
        self.message = message
        self.status = status
        super().__init__(self.message)


class AirQualityException(EnvironmentException):
    """Exception for air quality service errors"""
    def __init__(self, message: str, status: int = None, operation_code: str = None):
        self.message = message
        self.status = status
        self.operation_code = operation_code
        super().__init__(self.message)
