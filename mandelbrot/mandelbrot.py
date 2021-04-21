from datetime import datetime, timedelta
from time import sleep
from queue import Empty

import colorsys
import math
import multiprocessing as mp
import random
import threading

import pygame

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


def draw_pixels(pixel_queue, depth_queue):
    while True:
        pixel_group = pixel_queue.get()
        depth_group = []
        for (x, y, x_val, y_val, max_depth) in pixel_group:
            depth_group.append(((x, y), draw_pixel(x_val, y_val, max_depth)))
        depth_queue.put(depth_group)


def draw_pixel(x_val, y_val, max_depth):

    depth = calculate_depth(complex(x_val, y_val), max_depth)

    # Generate rainbow in hsv, then convert to rgb
    # Use 5/6 of spectrum to prevent overlapping back to red, stop at purple
    hsv = math.log((float(depth) / max_depth) * 9 + 1) * 5 / 6
    (r, g, b) = colorsys.hsv_to_rgb(hsv, 1.0, 1.0)

    return (r, g, b)


def calculate_depth(c: complex, max_depth: int) -> int:
    z = complex(0, 0)
    for i in range(0, max_depth):
        z = z ** 2 + c
        if abs(z) > 2:
            return i
    return max_depth


class MandelbrotThread(threading.Thread):
    def __init__(self, depth_queue):
        threading.Thread.__init__(self)

        self.x_min = INITIAL_X_MIN
        self.x_max = INITIAL_X_MAX
        self.y_min = INITIAL_Y_MIN
        self.y_max = INITIAL_Y_MAX
        self.max_depth = INITIAL_MAX_DEPTH

        self.pixel_queue = mp.Queue()
        self.depth_queue = depth_queue

        self.random_pixels_to_draw = random.sample(
            range(SCREEN_WIDTH * SCREEN_HEIGHT + 1), SCREEN_WIDTH * SCREEN_HEIGHT
        )

        self.generate_pixel_queue()

        # Set up processes
        self.processes = []
        for _ in range(PROCESSES):
            p = mp.Process(
                target=draw_pixels, args=(self.pixel_queue, self.depth_queue)
            )
            p.start()
            self.processes.append(p)

    def center(self, x_pixel, y_pixel):
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

    def zoom(self, percent):
        x_length = self.x_max - self.x_min
        y_length = self.y_max - self.y_min
        self.x_min += percent * x_length
        self.x_max -= percent * x_length
        self.y_min += percent * y_length
        self.y_max -= percent * y_length
        print(
            f"Zoomed to: (({self.x_min:.2e},{self.x_max:.2e}),({self.y_min:.2e},{self.y_max:.2e}))"
        )

    def center_and_zoom(self, x_pixel, y_pixel, percent):
        self.center(x_pixel, y_pixel)
        self.zoom(percent)

    def depth(self, val):
        self.max_depth *= val
        if self.max_depth < 2:
            self.max_depth = 2
        print(f"Depth changed to: {self.max_depth}")

    def generate_pixel_queue(self):
        pixel_group = []
        for pixel_num, pixel in enumerate(self.random_pixels_to_draw):
            x = int(pixel % SCREEN_WIDTH)
            y = int(pixel / SCREEN_HEIGHT)
            x_val = float(x) / (SCREEN_WIDTH) * (self.x_max - self.x_min) + self.x_min
            y_val = float(y) / (SCREEN_HEIGHT) * (self.y_max - self.y_min) + self.y_min
            pixel_group.append((x, y, x_val, y_val, self.max_depth))
            if pixel_num % GROUPINGS == 0:
                self.pixel_queue.put(pixel_group)
                pixel_group = []
        self.pixel_queue.put(pixel_group)
        pixel_group = []

    def clear_pixel_queue(self):
        try:
            while True:
                self.pixel_queue.get_nowait()
        except Empty:
            pass

    def clear_depth_queue(self):
        try:
            while True:
                self.depth_queue.get_nowait()
        except Empty:
            pass

    def reset_queues(self):
        self.clear_pixel_queue()
        self.clear_depth_queue()
        self.generate_pixel_queue()

    def run(self):
        # monitor values, regenerate pixel_queue if change detected
        x_min = 0
        x_max = 0
        y_min = 0
        y_max = 0
        max_depth = 0
        while True:
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


def main():
    # Set up window
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Mandelbrot")
    screen.fill((0, 0, 0))

    # Queue for drawing depths
    depth_queue = mp.Queue()

    # Thread for handling processes
    mandelbrot_thread = MandelbrotThread(depth_queue)
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
            for ((x, y), (r, g, b)) in depth_group:
                screen.set_at((x, y), (int(255 * r), int(255 * g), int(255 * b)))
            time = datetime.now()


if __name__ == "__main__":
    main()
