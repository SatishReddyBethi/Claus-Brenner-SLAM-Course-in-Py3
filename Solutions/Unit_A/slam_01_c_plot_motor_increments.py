# Plot the increments of the left and right motor.
# 01_c_plot_motor_increments.py
# Claus Brenner, 07 NOV 2012
import matplotlib.pyplot as plt
from lego_robot import LegoLogfile

if __name__ == '__main__':

    logfile = LegoLogfile()
    logfile.read("robot4_motors.txt")

    plt.plot(logfile.motor_ticks)
    plt.show()
