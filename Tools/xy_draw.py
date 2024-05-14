#coding:utf-8

import numpy as np

import matplotlib.pyplot as plt

from mpl_toolkits.mplot3d import Axes3D

def function_2(x,y):
    return x*y

# 这里的函数可以任意定义 return np.sum(x**2)

fig = plt.figure()

ax = Axes3D(fig)

x = np.arange(-50,50,0.2)

y = np.arange(-50,50,0.2)

X,Y = np.meshgrid(x,y)#创建网格，这个是关键

Z = function_2(X,Y)

plt.xlabel('x')

plt.ylabel('y')

ax.plot_surface(X,Y,Z,rstride=1,cstride=1,cmap='rainbow')

plt.show()