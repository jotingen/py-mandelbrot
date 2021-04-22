"""
Mandelbrot

Generate the mandelbrot fractal in a window
with the ability to zoom

"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from queue import Empty
from time import sleep
from typing import List, Tuple

import colorsys
import math
import multiprocessing as mp
import random
import sys
import threading

import pygame

@dataclass
class Pixel:
    """ Pixel class """
    x: int
    y: int
    def __call__(self) -> Tuple[int,int]:
        return (self.x, self.y)

@dataclass
class Color:
    """ Color class """
    r: float
    g: float
    b: float
    def __call__(self) -> Tuple[float,float,float]:
        return (self.r, self.g, self.b)


MOUSELEFT = 1
MOUSERIGHT = 3

PROCESSES = 11
GROUPINGS = 20

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000

INITIAL_X_MIN = -1.5
INITIAL_X_MAX = 1.5
INITIAL_Y_MIN = -1.5
INITIAL_Y_MAX = 1.5
INITIAL_MAX_DEPTH = 128


class MandelbrotProcess(mp.Process):
    """ Process with generates depth values at certain coordinates in a loop """

    def __init__( self,
    pixel_queue: "mp.Queue[List[Tuple[Pixel, float, float, int]]]",
    depth_queue: "mp.Queue[List[Tuple[Pixel,Color]]]",
    exit_event: mp.Event, # type: ignore
    ) -> None:
        mp.Process.__init__(self)
        self.pixel_queue = pixel_queue
        self.depth_queue = depth_queue
        self.exit_event = exit_event

    def run(self) -> None:

        while not self.exit_event.is_set(): # type: ignore
            try:
                pixel_group = self.pixel_queue.get(timeout=.1)
                depth_group: List[Tuple[Pixel, Color]] = []
                for (pixel, x_val, y_val, max_depth) in pixel_group:
                    depth_group.append((pixel, self.draw_pixel(x_val, y_val, max_depth)))
                self.depth_queue.put(depth_group)
            except Empty:
                pass
        print("Process done")


    def draw_pixel(
        self,
        x_val: float, y_val: float, max_depth: int
    ) -> Color:
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


class MandelbrotThread(threading.Thread):
    """ Thread for handling mandelbrot processes and maintaining state """

    def __init__(
            self, depth_queue: "mp.Queue[List[Tuple[Pixel,Color]]]", exit_event: threading.Event
    ) -> None:
        threading.Thread.__init__(self)

        self.x_min: float = INITIAL_X_MIN
        self.x_max: float = INITIAL_X_MAX
        self.y_min: float = INITIAL_Y_MIN
        self.y_max: float = INITIAL_Y_MAX
        self.max_depth: int = INITIAL_MAX_DEPTH

        self.pixel_queue: "mp.Queue[List[Tuple[Pixel, float, float, int]]]" = mp.Queue()
        self.depth_queue = depth_queue

        self.exit_event = exit_event

        self.random_pixels_to_draw = random.sample(
            range(SCREEN_WIDTH * SCREEN_HEIGHT + 1), SCREEN_WIDTH * SCREEN_HEIGHT
        )

        self.generate_pixel_queue()

        # Set up processes
        self.process_exit_event = mp.Event()
        self.processes = []
        for _ in range(PROCESSES):
            p = MandelbrotProcess(self.pixel_queue, self.depth_queue, self.process_exit_event)
            p.start()
            self.processes.append(p)

    def center(self, x_pixel: int, y_pixel: int) -> None:
        """ Center the image to a coordinate """

        x_center_new = self.x_min + x_pixel * (
            (self.x_max - self.x_min) / float(SCREEN_WIDTH)
        )
        y_center_new = self.y_min + y_pixel * (
            (self.y_max - self.y_min) / float(SCREEN_HEIGHT)
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

    def generate_pixel_queue(self) -> None:
        """ Fill pixel queue with pixels in a random order """

        pixel_group: List[Tuple[Pixel, float, float, int]] = []
        for pixel_num, position in enumerate(self.random_pixels_to_draw):
            pixel = Pixel(int(position % SCREEN_WIDTH), int(position / SCREEN_HEIGHT))
            x_val = float(pixel.x) / (SCREEN_WIDTH) * (self.x_max - self.x_min) + self.x_min
            y_val = float(pixel.y) / (SCREEN_HEIGHT) * (self.y_max - self.y_min) + self.y_min
            pixel_group.append((pixel, x_val, y_val, self.max_depth))
            if pixel_num % GROUPINGS == 0:
                self.pixel_queue.put(pixel_group)
                pixel_group = []
        self.pixel_queue.put(pixel_group)
        pixel_group = []

    def clear_pixel_queue(self) -> None:
        """ Clear the pixel queue """

        try:
            while True:
                self.pixel_queue.get_nowait()
        except Empty:
            pass

    def clear_depth_queue(self) -> None:
        """ Clear the depth queue """

        try:
            while True:
                self.depth_queue.get_nowait()
        except Empty:
            pass

    def reset_queues(self) -> None:
        """ Clear all queues and reloa pixel queue """

        self.clear_pixel_queue()
        self.clear_depth_queue()
        self.generate_pixel_queue()

    def run(self) -> None:
        # monitor values, regenerate pixel_queue if change detected
        x_min: float = 0
        x_max: float = 0
        y_min: float = 0
        y_max: float = 0
        max_depth: int = 0
        while not self.exit_event.is_set():
            if (
               x_min != self.x_min
                or x_max != self.x_max
                or y_min != self.y_min
                or y_max != self.y_max
                or max_depth != self.max_depth
            ):

                x_min = self.x_min
                x_max = self.x_max
                y_min = self.y_min
                y_max = self.y_max
                max_depth = self.max_depth

                self.reset_queues()

            sleep(0.5)

        self.process_exit_event.set()
        for p in self.processes:
            p.terminate()

        print("Thread done")


def main() -> None:
    """ Main function """
    # Set up window
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Mandelbrot")
    screen.fill((0, 0, 0))

    # Queue for drawing depths
    depth_queue: "mp.Queue[List[Tuple[Pixel,Color]]]" = mp.Queue()

    # Thread for handling processes
    mandelbrot_thread_exit = threading.Event()
    mandelbrot_thread = MandelbrotThread(depth_queue, mandelbrot_thread_exit)
    mandelbrot_thread.start()

    # Main loop
    running = True
    frame_start_time = datetime.now()
    while running:
        # Redraw/check events at 60 fps
        time = datetime.now()
        if time - frame_start_time >= timedelta(microseconds=16666):
            pygame.display.flip()
            frame_start_time = time

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # Center and Zoom In
                if event.type == pygame.MOUSEBUTTONUP and event.button == MOUSELEFT:
                    (x_pixel, y_pixel) = pygame.mouse.get_pos()
                    mandelbrot_thread.center_and_zoom(x_pixel, y_pixel, 0.2)
                # Center and Zoom Out
                if event.type == pygame.MOUSEBUTTONUP and event.button == MOUSERIGHT:
                    (x_pixel, y_pixel) = pygame.mouse.get_pos()
                    mandelbrot_thread.center_and_zoom(x_pixel, y_pixel, 1 / 0.2)
                # Decrease depth
                if event.type == pygame.KEYDOWN and event.key == pygame.K_j:
                    mandelbrot_thread.depth(0.5)
                # Increase depth
                if event.type == pygame.KEYDOWN and event.key == pygame.K_k:
                    mandelbrot_thread.depth(2)

        # If there is something in the depth queue, draw it
        # Force a break to redraw
        time = datetime.now()
        while not depth_queue.empty() and not (
            time - frame_start_time >= timedelta(microseconds=16666)
        ):
            depth_group = depth_queue.get()
            for (pixel, color) in depth_group:
                screen.set_at(pixel(), (int(255 * color.r), int(255 * color.g), int(255 * color.b)))
            time = datetime.now()

    mandelbrot_thread_exit.set()
    mandelbrot_thread.join()
    pygame.display.quit()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
