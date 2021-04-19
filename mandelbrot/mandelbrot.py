import typing

def calculate_depth(c: complex, max_depth: int) -> int:
    z = complex(0,0)
    for i in range(0,max_depth):
        z = z**2 + c
        if abs(z) > 2:
            return i
    return max_depth

x_steps:int = 100
y_steps:int = 30
max_depth:int = 1024
for y in range(y_steps):
    y_val = -float(y)/(y_steps-1)*3+1.5
    for x in range(x_steps):
        x_val = float(x)/(x_steps-1)*3-1.5
        depth = calculate_depth(complex(x_val,y_val),max_depth)
        if depth == max_depth:
            print("x",end='')
        elif depth > 10:
            print(".",end='')
        else:
            print(" ",end='')
    print()

