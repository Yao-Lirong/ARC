import random
import numpy as np
n = random.randint(1,5)
color = 9
length = 11
def get_random_gray_point():
    x = random.randint(1,11)
    y = random.randint(1,11)
    c = random.randint(1,color)
    halo = np.random.random([3,3])
    halo = (halo > 0.5) * c
    return x, y, c, halo

gray = []
for i in range(n):
    gray.append(get_random_gray_point())

canvas = np.zeros([20,20])

for x, y, c, halo in gray:
    canvas[x-1:x+2, y-1:y+2] = halo
    canvas[x,y] = -1

canvas
