from datetime import datetime, timedelta
from time import sleep
import colorsys
import pygame
import random
import threading
import typing

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


#Text version
#x_steps:int = 100
#y_steps:int = 30
#max_depth:int = 16
#for y in range(y_steps+1):
#    y_val = -float(y)/(y_steps)*3+1.5
#    for x in range(x_steps+1):
#        x_val = float(x)/(x_steps)*3-1.5
#        depth = calculate_depth(complex(x_val,y_val),max_depth)
#        if depth == max_depth:
#            print("x",end='')
#        elif depth > 10:
#            print(".",end='')
#        else:
#            print(" ",end='')
#    print()

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

pygame.display.flip()

# #initial draw
# frame_start_time = datetime.now()
# for step in random.sample(range(width*height+1),width*height):
#     x = int(step%width)
#     y = int(step/height)
#     x_val = float(x)/(width)*(x_max-x_min)+x_min
#     y_val = float(y)/(height)*(y_max-y_min)+y_min
#     depth = calculate_depth(complex(x_val,y_val),max_depth)
# 
#     #Generate rainbow in hsv, then convert to rgb
#     #Use 5/6 of spectrum to prevent overlapping back to red, stop at purple
#     hsv = float(depth)/max_depth*5/6
#     (r,g,b) = colorsys.hsv_to_rgb(hsv, 1.0, 1.0)
#     #print(f"{depth}\t{float(depth)/max_depth)}\t{r}\t{g}\t{b}")
#     screen.set_at((x,y),(int(255 * r), int(255 * g), int(255 * b)))
#     time = datetime.now()
#     if time - frame_start_time >= timedelta(microseconds=16666):
#         pygame.display.flip()
#         frame_start_time = time
# 
# pygame.display.flip()

pygame.font.init()
font = pygame.font.SysFont(None, 50)

def draw_pixel(x,y,screen):

        x_val = float(x)/(width)*(x_max-x_min)+x_min
        y_val = float(y)/(height)*(y_max-y_min)+y_min
        depth = calculate_depth(complex(x_val,y_val),max_depth)

        #Generate rainbow in hsv, then convert to rgb
        #Use 5/6 of spectrum to prevent overlapping back to red, stop at purple
        hsv = float(depth)/max_depth*5/6
        (r,g,b) = colorsys.hsv_to_rgb(hsv, 1.0, 1.0)
        #print(f"{depth}\t{float(depth)/max_depth)}\t{r}\t{g}\t{b}")
        screen.set_at((x,y),(int(255 * r), int(255 * g), int(255 * b)))

running = True
frame_start_time = datetime.now()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONUP and event.button == MOUSELEFT:
            print('L',pygame.mouse.get_pos())
            #Center
            (x_pixel, y_pixel) = pygame.mouse.get_pos()
            x_center_new = x_min+x_pixel*((x_max-x_min)/float(width))
            y_center_new = y_min+y_pixel*((y_max-y_min)/float(height))
            #print('ORIG')
            #print((x_max+x_min)/2,(y_max+y_min)/2)
            #print((x_min,x_max),(y_min,y_max),x_max-x_min,y_max-y_min)
            #print("CALC")
            #print(x_center_new,y_center_new)
            x_length = (x_max-x_min)
            y_length = (y_max-y_min)
            x_min = x_center_new-x_length/2
            x_max = x_center_new+x_length/2
            y_min = y_center_new-y_length/2
            y_max = y_center_new+y_length/2
            #print("NEW")
            #print((x_max+x_min)/2,(y_max+y_min)/2)
            #print((x_min,x_max),(y_min,y_max),x_max-x_min,y_max-y_min)
            #Scale
            x_min += .2*x_length
            x_max -= .2*x_length
            y_min += .2*y_length
            y_max -= .2*y_length
        if event.type == pygame.MOUSEBUTTONUP and event.button == MOUSERIGHT:
            print('R',pygame.mouse.get_pos())
            #Center
            (x_pixel, y_pixel) = pygame.mouse.get_pos()
            x_center_new = x_min+x_pixel*((x_max-x_min)/float(width))
            y_center_new = y_min+y_pixel*((y_max-y_min)/float(height))
            #print('ORIG')
            #print((x_max+x_min)/2,(y_max+y_min)/2)
            #print((x_min,x_max),(y_min,y_max),x_max-x_min,y_max-y_min)
            #print("CALC")
            #print(x_center_new,y_center_new)
            x_length = (x_max-x_min)
            y_length = (y_max-y_min)
            x_min = x_center_new-x_length/2
            x_max = x_center_new+x_length/2
            y_min = y_center_new-y_length/2
            y_max = y_center_new+y_length/2
            #print("NEW")
            #print((x_max+x_min)/2,(y_max+y_min)/2)
            #print((x_min,x_max),(y_min,y_max),x_max-x_min,y_max-y_min)
            #Scale
            x_min += 1/.2*x_length
            x_max -= 1/.2*x_length
            y_min += 1/.2*y_length
            y_max -= 1/.2*y_length

    # mb_thread = mandelbrotThread()
    # mb_thread.start()
    # mb_thread.join()

    for step in random.sample(range(width*height+1),width*height):
        x = int(step%width)
        y = int(step/height)
        draw_pixel(x,y,screen)

    frame_stop_time = datetime.now()
    fps = 1/(frame_stop_time.timestamp()-frame_start_time.timestamp())
    frame_start_time = frame_stop_time

    text_fps = font.render(str(fps), True, (0, 255, 255))
    screen.blit(text_fps, (100,100))

    pygame.display.flip()
