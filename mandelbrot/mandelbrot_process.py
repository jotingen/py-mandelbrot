""" Mandelbrot Process Module """

from queue import Empty
from typing import List, Tuple

import colorsys
import math
import multiprocessing as mp

from .pixel import Pixel
from .color import Color

class MandelbrotProcess(mp.Process):
    """ Process with generates depth values at certain coordinates in a loop """

    def __init__(
        self,
        pixel_queue: "mp.Queue[List[Tuple[Pixel, float, float, int]]]",
        depth_queue: "mp.Queue[List[Tuple[Pixel,Color]]]",
        exit_event: mp.Event,  # type: ignore
    ) -> None:
        mp.Process.__init__(self)
        self.pixel_queue = pixel_queue
        self.depth_queue = depth_queue
        self.exit_event = exit_event

    def run(self) -> None:

        while not self.exit_event.is_set():  # type: ignore
            try:
                #count += 1
                #print("process start", count)
                pixel_group = self.pixel_queue.get(timeout=0.1)
                depth_group: List[Tuple[Pixel, Color]] = []
                for (pixel, x_val, y_val, max_depth) in pixel_group:
                    depth_group.append(
                        (pixel, self.draw_pixel(x_val, y_val, max_depth))
                    )
                self.depth_queue.put(depth_group)
                #print("process end", count)
            except Empty:
                pass
            except OSError:
                #print("process end OSError", count)
                return
            except ValueError:
                #print("process end ValueError", count)
                return
        print("Process done")

    def draw_pixel(self, x_val: float, y_val: float, max_depth: int) -> Color:
        """ Take pixel, calculate deth up to max depth, and output rgb value """

        depth = self.calculate_depth(complex(x_val, y_val), max_depth)

        # Generate rainbow in hsv, then convert to rgb
        # Use 5/6 of spectrum to prevent overlapping back to red, stop at purple
        hsv = math.log((float(depth) / max_depth) * 9 + 1) * 5 / 6
        return Color(*colorsys.hsv_to_rgb(hsv, 1.0, 1.0))

    def calculate_depth(self, c: complex, max_depth: int) -> int:
        """ Run mandelbrot calculation up to max_depth """

        z = complex(0, 0)
        for i in range(0, max_depth):
            z = z ** 2 + c
            if abs(z) > 2:
                return i
        return max_depth
