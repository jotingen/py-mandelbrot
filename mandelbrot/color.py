""" Color module """
from dataclasses import dataclass
from typing import Tuple

@dataclass
class Color:
    """ Color class """

    r: float
    g: float
    b: float

    def __call__(self) -> Tuple[float, float, float]:
        return (self.r, self.g, self.b)
