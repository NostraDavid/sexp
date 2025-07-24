from attr import dataclass
from returns.maybe import Maybe, Nothing, maybe
from returns.result import Result, Success, Failure

@dataclass(frozen=True)
class Hex:
    """Class representing a hexadecimal value in S-expression format."""
    def __init__(self, value: int) -> Result["Hex"]:
        self.value = value
        if not (0 <= value <= 0xFF):
            return Failure(ValueError("Hex value must be between 0x00 and 0xFF"))
        return Success(self)
