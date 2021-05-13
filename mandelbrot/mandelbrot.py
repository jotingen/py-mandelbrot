"""
Mandelbrot

Generate the mandelbrot fractal in a window
with the ability to zoom

"""

from datetime import datetime, timedelta
from typing import List, Tuple
from time import sleep

import multiprocessing as mp
import random
import sys
import threading

import pygame

from .pixel             import Pixel            
from .color             import Color            
from .mandelbrot_thread  import MandelbrotThread 



MOUSELEFT = 1
MOUSERIGHT = 3

PROCESSES = 11
GROUPINGS = 40

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000

INITIAL_X_MIN = -1.5
INITIAL_X_MAX = 1.5
INITIAL_Y_MIN = -1.5
INITIAL_Y_MAX = 1.5
INITIAL_MAX_DEPTH = 128




def load_pending_queue(pending_queue: "mp.Queue[List[Pixel]]") -> None:
    """ Fill pixel queue with pixels in a random order """

    random_pixels_to_draw = random.sample(
        range(SCREEN_WIDTH * SCREEN_HEIGHT + 1), SCREEN_WIDTH * SCREEN_HEIGHT
    )
    pending_group: List[Pixel] = []
    for pixel_num, position in enumerate(random_pixels_to_draw):
        pixel = Pixel(int(position % SCREEN_WIDTH), int(position / SCREEN_HEIGHT))
        pending_group.append(pixel)
        if pixel_num % GROUPINGS == 0:
            pending_queue.put(pending_group)
            pending_group = []


def main() -> None:
    """ Main function """
    # Set up window
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Mandelbrot")
    screen.fill((0, 0, 0))

    # Queue for drawing depths
    depth_queue: "mp.Queue[List[Tuple[Pixel,Color]]]" = mp.Queue(PROCESSES * 20)
    pending_queue: "mp.Queue[List[Pixel]]" = mp.Queue()
    load_pending_queue(pending_queue)

    # Thread for handling processes
    mandelbrot_thread_exit = threading.Event()
    mandelbrot_thread = MandelbrotThread(
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        INITIAL_X_MIN,
        INITIAL_X_MAX,
        INITIAL_Y_MIN,
        INITIAL_Y_MAX,
        INITIAL_MAX_DEPTH,
        pending_queue, depth_queue, mandelbrot_thread_exit
    )
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
                    mandelbrot_thread.center_and_zoom(x_pixel, y_pixel, 0.4)
                # Center and Zoom Out
                if event.type == pygame.MOUSEBUTTONUP and event.button == MOUSERIGHT:
                    (x_pixel, y_pixel) = pygame.mouse.get_pos()
                    mandelbrot_thread.center_and_zoom(x_pixel, y_pixel, 1 / 0.4)
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
            pending_group: List[Pixel] = []
            for (pixel, color) in depth_group:
                screen.set_at(
                    pixel(),
                    (int(255 * color.r), int(255 * color.g), int(255 * color.b)),
                )
                pending_group.append(pixel)
            pending_queue.put(pending_group)
            time = datetime.now()

    pending_queue.close()
    depth_queue.cancel_join_thread()
    print("pending queue closed")
    depth_queue.close()
    pending_queue.cancel_join_thread()
    print("depth queue closed")
    mandelbrot_thread_exit.set()
    print("thread sent exit")
    #sleep(1)

    print("Waiting for thread to join")
    while mandelbrot_thread.is_alive():
        print("thread alive")
        sleep(1)
    mandelbrot_thread.join()
    pygame.display.quit()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
