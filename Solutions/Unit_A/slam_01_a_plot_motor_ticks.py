# Plot the ticks from the left and right motor.
# 01_a_plot_motor_ticks.py
# Claus Brenner, 07 NOV 2012
import matplotlib.pyplot as plt

if __name__ == '__main__':
    # Read all ticks of left and right motor.
    # Format is:
    # M timestamp[in ms] pos-left[in ticks] * * * pos-right[in ticks] ...
    # so we are interested in field 2 (left) and 6 (right).
    f = open("robot4_motors.txt")
    left_list = []
    right_list = []
    for l in f:
        sp = l.split()
        left_list.append(int(sp[2]))
        right_list.append(int(sp[6]))

    plt.plot(left_list)
    plt.plot(right_list)
    plt.show()
