from datetime import datetime, timedelta
from time import sleep
from queue import Empty
import colorsys
import math
import multiprocessing as mp
import pygame
import random
import threading
import typing
import sys

MOUSELEFT = 1
MOUSERIGHT = 3

def calculate_depth(c: complex, max_depth: int) -> int:
    z = complex(0,0)
    for i in range(0,max_depth):
        z = z**2 + c
        if abs(z) > 2:
            return i
    return max_depth

class mandelbrotThread(threading.Thread):
    def __init(self):
        threading.Thread.__init__(self)

    def run(self):
        print("Test")
        sleep(.5)
        print("Done")


background_colour = (0,0,0)
width:int = 1000
height:int = 1000
x_min = -1
x_max = 1
y_min = -1
y_max = 1
max_depth:int = 8

screen = pygame.display.set_mode((width,height))
pygame.display.set_caption('Mandelbrot')
screen.fill(background_colour)

def draw_pixels(pixel_queue, depth_queue):
    while True:
        (x,y) = pixel_queue.get()
        draw_pixel(x,y,depth_queue)

def draw_pixel(x,y,depth_queue):

    x_val = float(x)/(width)*(x_max-x_min)+x_min
    y_val = float(y)/(height)*(y_max-y_min)+y_min
    depth = calculate_depth(complex(x_val,y_val),max_depth)

    #Generate rainbow in hsv, then convert to rgb
    #Use 5/6 of spectrum to prevent overlapping back to red, stop at purple
    hsv = math.log((float(depth)/max_depth)*9+1)*5/6
    (r,g,b) = colorsys.hsv_to_rgb(hsv, 1.0, 1.0)

    depth_queue.put(((x,y),(r,g,b)))

running = True
frame_start_time = datetime.now()
random_pixels_to_draw = random.sample(range(width*height+1),width*height)


#Queues for drawing processes
pixel_queue = mp.Queue()
depth_queue = mp.Queue()

def clear_queue(q):
    try:
        while True:
            q.get_nowait()
    except Empty:
        pass

#Set up drawing processes
processes = []
for proc in range(11):
    p = mp.Process(target=draw_pixels, args=(pixel_queue,depth_queue))
    p.start()
    processes.append(p)

#Initial load of pixel queue
for pixel in random_pixels_to_draw:
    x = int(pixel%width)
    y = int(pixel/height)
    pixel_queue.put((x,y))

while running:
    def reset_pixel_queue():
        clear_queue(pixel_queue)
        for pixel in random_pixels_to_draw:
            x = int(pixel%width)
            y = int(pixel/height)
            pixel_queue.put((x,y))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONUP and event.button == MOUSELEFT:
            print('L',pygame.mouse.get_pos())
            #Center
            (x_pixel, y_pixel) = pygame.mouse.get_pos()
            x_center_new = x_min+x_pixel*((x_max-x_min)/float(width))
            y_center_new = y_min+y_pixel*((y_max-y_min)/float(height))
            x_length = (x_max-x_min)
            y_length = (y_max-y_min)
            x_min = x_center_new-x_length/2
            x_max = x_center_new+x_length/2
            y_min = y_center_new-y_length/2
            y_max = y_center_new+y_length/2
            #Scale
            x_min += .2*x_length
            x_max -= .2*x_length
            y_min += .2*y_length
            y_max -= .2*y_length
            reset_pixel_queue()
        if event.type == pygame.MOUSEBUTTONUP and event.button == MOUSERIGHT:
            print('R',pygame.mouse.get_pos())
            #Center
            (x_pixel, y_pixel) = pygame.mouse.get_pos()
            x_center_new = x_min+x_pixel*((x_max-x_min)/float(width))
            y_center_new = y_min+y_pixel*((y_max-y_min)/float(height))
            x_length = (x_max-x_min)
            y_length = (y_max-y_min)
            x_min = x_center_new-x_length/2
            x_max = x_center_new+x_length/2
            y_min = y_center_new-y_length/2
            y_max = y_center_new+y_length/2
            #Scale
            x_min += 1/.2*x_length
            x_max -= 1/.2*x_length
            y_min += 1/.2*y_length
            y_max -= 1/.2*y_length
            reset_pixel_queue()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_j:
            max_depth = int(max_depth/2)
            if max_depth < 2:
                max_depth = 2
            reset_pixel_queue()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_k:
            max_depth = int(max_depth*2)
            reset_pixel_queue()

    #If there is something in the depth queue, draw it
    #Force a break every hundred pixels
    counter = 0
    while not depth_queue.empty() and counter < 100:
        ((x,y),(r,g,b)) = depth_queue.get()
        screen.set_at((x,y),(int(255 * r), int(255 * g), int(255 * b)))
        counter += 1

    #Redraw at 60 fps
    time = datetime.now()
    if time - frame_start_time >= timedelta(microseconds=2*16666):
        pygame.display.flip()
        if pixel_queue.empty():
            sleep(.5)
        frame_start_time = time

