from dataclasses import dataclass
from typing import Tuple

@dataclass
class Pixel:
    """ Pixel class """

    x: int
    y: int

    def __call__(self) -> Tuple[int, int]:
        return (self.x, self.y)
