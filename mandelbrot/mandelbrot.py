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

SCREEN_WIDTH:int = 1000
SCREEN_HEIGHT:int = 1000

INITIAL_X_MIN = -1.5
INITIAL_X_MAX = 1.5
INITIAL_Y_MIN = -1.5
INITIAL_Y_MAX = 1.5
INITIAL_MAX_DEPTH:int = 8

class MandelbrotThread(threading.Thread):
    def __init__(self, depth_queue):
        threading.Thread.__init__(self)

        self.x_min     = INITIAL_X_MIN
        self.x_max     = INITIAL_X_MAX
        self.y_min     = INITIAL_Y_MIN
        self.y_max     = INITIAL_Y_MAX
        self.max_depth = INITIAL_MAX_DEPTH

        self.pixel_queue = mp.Queue()
        self.depth_queue = depth_queue

        self.generate_pixel_queue()

        #Set up processes
        self.processes = []
        for proc in range(PROCESSES):
            p = mp.Process(target=draw_pixels, args=(self.pixel_queue,self.depth_queue))
            p.start()
            self.processes.append(p)

    def zoom(self, x_pixel, y_pixel, percent):
        x_center_new = self.x_min+x_pixel*((self.x_max-self.x_min)/float(SCREEN_WIDTH))
        y_center_new = self.y_min+y_pixel*((self.y_max-self.y_min)/float(SCREEN_HEIGHT))
        x_length = (self.x_max-self.x_min)
        y_length = (self.y_max-self.y_min)
        self.x_min = x_center_new-x_length/2
        self.x_max = x_center_new+x_length/2
        self.y_min = y_center_new-y_length/2
        self.y_max = y_center_new+y_length/2
        #Scale
        self.x_min += percent*x_length
        self.x_max -= percent*x_length
        self.y_min += percent*y_length
        self.y_max -= percent*y_length
    
    def center(self, x_pixel, y_pixel):
        pass

    def depth(self, val):
        self.max_depth *= val
        if self.max_depth < 2:
            self.max_depth = 2

    def generate_pixel_queue(self):
        random_pixels_to_draw = random.sample(range(SCREEN_WIDTH*SCREEN_HEIGHT+1),SCREEN_WIDTH*SCREEN_HEIGHT)
        while len(random_pixels_to_draw):
            pixel_group = []
            for _ in range(GROUPINGS):
                if len(random_pixels_to_draw):
                    pixel = random_pixels_to_draw.pop()
                    x = int(pixel%SCREEN_WIDTH)
                    y = int(pixel/SCREEN_HEIGHT)
                    x_val = float(x)/(SCREEN_WIDTH)*(self.x_max-self.x_min)+self.x_min
                    y_val = float(y)/(SCREEN_HEIGHT)*(self.y_max-self.y_min)+self.y_min
                    pixel_group.append((x,y,x_val,y_val,self.max_depth))
            self.pixel_queue.put(pixel_group)

    def clear_pixel_queue(self):
        try:
            while True:
                self.pixel_queue.get_nowait()
        except Empty:
            pass

    def reset_pixel_queue(self):
        self.clear_pixel_queue()
        self.generate_pixel_queue()

    def draw_pixels(pixel_queue, depth_queue):
        while True:
            pixel_group = pixel_queue.get()
            depth_group = []
            for (x,y,x_val,y_val,max_depth) in pixel_group:
                depth_group.append(((x,y),draw_pixel(x_val,y_val,max_depth)))
            depth_queue.put(depth_group)

    def draw_pixel(x_val,y_val,max_depth):

        depth = calculate_depth(complex(x_val,y_val),max_depth)

        #Generate rainbow in hsv, then convert to rgb
        #Use 5/6 of spectrum to prevent overlapping back to red, stop at purple
        hsv = math.log((float(depth)/max_depth)*9+1)*5/6
        (r,g,b) = colorsys.hsv_to_rgb(hsv, 1.0, 1.0)

        return (r,g,b)

    def calculate_depth(c: complex, max_depth: int) -> int:
        z = complex(0,0)
        for i in range(0,max_depth):
            z = z**2 + c
            if abs(z) > 2:
                return i
        return max_depth

    def run(self):
        #monitor values, regenerate pixel_queue if change detected
        x_min     = 0
        x_max     = 0
        y_min     = 0
        y_max     = 0
        max_depth = 0
        while True:
            if (x_min     != self.x_min     or
                x_max     != self.x_max     or
                y_min     != self.y_min     or
                y_max     != self.y_max     or
                max_depth != self.max_depth):

                print("RESET")
                x_min     = self.x_min    
                x_max     = self.x_max    
                y_min     = self.y_min    
                y_max     = self.y_max    
                max_depth = self.max_depth

                self.reset_pixel_queue()

            sleep(.5)


screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption('Mandelbrot')
screen.fill((0,0,0))


#Queue for drawing depths
depth_queue = mp.Queue()

mandelbrot_thread = MandelbrotThread(depth_queue)
mandelbrot_thread.start()

running = True
frame_start_time = datetime.now()
while running:
    #Redraw/check events at 60 fps
    time = datetime.now()
    if time - frame_start_time >= timedelta(microseconds=16666):
        pygame.display.flip()
        frame_start_time = time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONUP and event.button == MOUSELEFT:
                print('LMOUSE',pygame.mouse.get_pos())
                (x_pixel, y_pixel) = pygame.mouse.get_pos()
                mandelbrot_thread.zoom(x_pixel, y_pixel,.2)
            if event.type == pygame.MOUSEBUTTONUP and event.button == MOUSERIGHT:
                print('RMOUSE',pygame.mouse.get_pos())
                (x_pixel, y_pixel) = pygame.mouse.get_pos()
                mandelbrot_thread.zoom(x_pixel, y_pixel,1/.2)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_j:
                print("J")
                mandelbrot_thread.depth(.5)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_k:
                print("K")
                mandelbrot_thread.depth(2)

    #If there is something in the depth queue, draw it
    #Force a break to redraw
    time = datetime.now()
    while not depth_queue.empty() and not (time - frame_start_time >= timedelta(microseconds=16666)):
        depth_group = depth_queue.get()
        for ((x,y),(r,g,b)) in depth_group:
            screen.set_at((x,y),(int(255 * r), int(255 * g), int(255 * b)))
        time = datetime.now()


