""" Mendelbrot Thread Module """

from queue import Empty
from typing import List, Tuple

import multiprocessing as mp
import random
import threading

from .pixel             import Pixel
from .color             import Color            
from .mandelbrot_process import MandelbrotProcess

PROCESSES = 11

class MandelbrotThread(threading.Thread):
    """ Thread for handling mandelbrot processes and maintaining state """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        max_depth: int,
        pending_queue: "mp.Queue[List[Pixel]]",
        depth_queue: "mp.Queue[List[Tuple[Pixel,Color]]]",
        exit_event: threading.Event,
    ) -> None:
        threading.Thread.__init__(self)

        self.screen_width: float = screen_width
        self.screen_height: float = screen_height

        self.x_min: float = x_min
        self.x_max: float = x_max
        self.y_min: float = y_min
        self.y_max: float = y_max
        self.max_depth: int = max_depth

        self.pending_queue = pending_queue
        self.pixel_queue: "mp.Queue[List[Tuple[Pixel, float, float, int]]]" = mp.Queue(
            500
        )
        self.depth_queue = depth_queue

        self.exit_event = exit_event

        self.random_pixels_to_draw = random.sample(
            range(screen_width * screen_height + 1), screen_width * screen_height
        )

        # self.generate_pixel_queue()

        # Set up processes
        self.process_exit_event = mp.Event()
        self.processes = []
        for _ in range(PROCESSES):
            p = MandelbrotProcess(
                self.pixel_queue, self.depth_queue, self.process_exit_event
            )
            p.start()
            self.processes.append(p)

    def center(self, x_pixel: int, y_pixel: int) -> None:
        """ Center the image to a coordinate """

        x_center_new = self.x_min + x_pixel * (
            (self.x_max - self.x_min) / float(self.screen_width)
        )
        y_center_new = self.y_min + y_pixel * (
            (self.y_max - self.y_min) / float(self.screen_height)
        )
        x_length = self.x_max - self.x_min
        y_length = self.y_max - self.y_min
        self.x_min = x_center_new - x_length / 2
        self.x_max = x_center_new + x_length / 2
        self.y_min = y_center_new - y_length / 2
        self.y_max = y_center_new + y_length / 2
        print(
            f"Centered to: ({(self.x_max+self.x_min)/2:.2e},{-(self.y_max+self.y_min)/2:.2e})"
        )

    def zoom(self, percent: float) -> None:
        """ Zoom in or out """

        x_length = self.x_max - self.x_min
        y_length = self.y_max - self.y_min
        self.x_min += percent * x_length
        self.x_max -= percent * x_length
        self.y_min += percent * y_length
        self.y_max -= percent * y_length
        print(
            f"Zoomed to: (({self.x_min:.2e},{self.x_max:.2e}),({self.y_min:.2e},{self.y_max:.2e}))"
        )

    def center_and_zoom(self, x_pixel: int, y_pixel: int, percent: float) -> None:
        """ center and then zoom """

        self.center(x_pixel, y_pixel)
        self.zoom(percent)

    def depth(self, val: float) -> None:
        """ Change the max_depth by multiplying current value by val """

        self.max_depth = int(self.max_depth * val)
        if self.max_depth < 2:
            self.max_depth = 2
        print(f"Depth changed to: {self.max_depth}")

    def run(self) -> None:

        while not self.exit_event.is_set():

            try:
                count = 0
                while True:
                    #print("working start", count)
                    count += 1
                    pending_group = self.pending_queue.get_nowait()
                    pixel_group: List[Tuple[Pixel, float, float, int]] = []
                    for pixel in pending_group:
                        x_val = (
                            float(pixel.x) / (self.screen_width) * (self.x_max - self.x_min)
                            + self.x_min
                        )
                        y_val = (
                            float(pixel.y) / (self.screen_height) * (self.y_max - self.y_min)
                            + self.y_min
                        )
                        pixel_group.append((pixel, x_val, y_val, self.max_depth))
                    self.pixel_queue.put(pixel_group)
                    #print("working end", count)
            except Empty:
                #print("working end Empty", count)
                pass
            except OSError:
                print("working end OSError", count)
                pass
            except ValueError:
                print("working end ValueError", count)
                pass

        print("thread exiting")
        self.pixel_queue.close()
        print("pixel_queue_closed")
        self.process_exit_event.set()
        print("processes sent exit")
        for p in self.processes:
            p.terminate()
            print("process terminated")
        for p in self.processes:
            p.join()
            print("process joined")
        #self.pixel_queue.cancel_join_thread()
        #print("CANCELLED")

        print("Thread done")
