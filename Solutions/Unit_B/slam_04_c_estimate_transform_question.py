# For each cylinder in the scan, find its cartesian coordinates,
# in the world coordinate system.
# Find the closest pairs of cylinders from the scanner and cylinders
# from the reference, and the optimal transformation which aligns them.
# Then, output the scanned cylinders, using this transform.
# 04_c_estimate_transform
# Claus Brenner, 14 NOV 2012
from lego_robot import *
from slam_b_library import filter_step
from slam_04_a_project_landmarks import\
     compute_scanner_cylinders, write_cylinders
from math import sqrt
import os

# Given a list of cylinders (points) and reference_cylinders:
# For every cylinder, find the closest reference_cylinder and add
# the index pair (i, j), where i is the index of the cylinder, and
# j is the index of the reference_cylinder, to the result list.
# This is the function developed in slam_04_b_find_cylinder_pairs.

def dist(point1,point2):
    return sqrt(((point2[0]-point1[0])**2) + ((point2[1]-point1[1])**2)).real

def find_cylinder_pairs(cylinders, reference_cylinders, max_radius):
    cylinder_pairs = []

    # --->>> Insert here your code from the last question,
    # slam_04_b_find_cylinder_pairs.
    for i in range(len(cylinders)):
            min_dist = 100000
            closest_cyl = -1
            for j in range(len(reference_cylinders)):
                distance = dist(cylinders[i],reference_cylinders[j])
                if(distance<min_dist):
                    min_dist = distance
                    closest_cyl = j

            if(min_dist < max_radius and closest_cyl != -1):
                cylinder_pairs.append((i,closest_cyl))

    return cylinder_pairs

# Given a point list, return the center of mass.
def compute_center(point_list):
    # Safeguard against empty list.
    if not point_list:
        return (0.0, 0.0)
    # If not empty, sum up and divide.
    sx = sum([p[0] for p in point_list])
    sy = sum([p[1] for p in point_list])
    return (float(sx) / len(point_list), float(sy) / len(point_list))

# Given a left_list of points and a right_list of points, compute
# the parameters of a similarity transform: scale, rotation, translation.
# If fix_scale is True, use the fixed scale of 1.0.
# The returned value is a tuple of:
# (scale, cos(angle), sin(angle), x_translation, y_translation)
# i.e., the rotation angle is not given in radians, but rather in terms
# of the cosine and sine.
def estimate_transform(left_list, right_list, fix_scale = False):
    # Compute left and right center.
    lc = compute_center(left_list)
    rc = compute_center(right_list)
    Px = 0
    Py = 0
    ll = 0
    rr = 0
    m = len(left_list)
    # --->>> Insert here your code to compute lambda, c, s and tx, ty.
    for j in range(m):
        # left prime
        Lx_prime = left_list[j][0]-lc[0]
        Ly_prime = left_list[j][1]-lc[1]
        # right prime
        Rx_prime = right_list[j][0]-rc[0]
        Ry_prime = right_list[j][1]-rc[1]

        Px += (Rx_prime * Lx_prime) + (Ry_prime * Ly_prime)
        Py += (Ry_prime * Lx_prime) - (Rx_prime * Ly_prime)
        rr = (Rx_prime * Rx_prime) + (Ry_prime * Ry_prime)
        ll = (Lx_prime * Lx_prime) + (Ly_prime * Ly_prime)

    la = 1

    if(rr == 0 or ll == 0):
        return None

    if(not fix_scale):
        la = sqrt(rr/ll)

    c = Px/sqrt((Px**2) + (Py**2))
    s = Py/sqrt((Px**2) + (Py**2))
    
    tx = rc[0] - (la * ((c * lc[0]) - (s * lc[1])))
    ty = rc[1] - (la * ((s * lc[0]) + (c * lc[1])))
    return la, c, s, tx, ty

# Given a similarity transformation:
# trafo = (scale, cos(angle), sin(angle), x_translation, y_translation)
# and a point p = (x, y), return the transformed point.
def apply_transform(trafo, p):
    la, c, s, tx, ty = trafo
    lac = la * c
    las = la * s
    x = lac * p[0] - las * p[1] + tx
    y = las * p[0] + lac * p[1] + ty
    return (x, y)


if __name__ == '__main__':
    # The constants we used for the filter_step.
    scanner_displacement = 30.0
    ticks_to_mm = 0.349
    robot_width = 150.0

    # The constants we used for the cylinder detection in our scan.    
    minimum_valid_distance = 20.0
    depth_jump = 100.0
    cylinder_offset = 90.0

    # The maximum distance allowed for cylinder assignment.
    max_cylinder_distance = 300.0

    # The start pose we obtained miraculously.
    pose = (1850.0, 1897.0, 3.717551306747922)

    # Read the logfile which contains all scans.
    logfile = LegoLogfile()
    logfile.read("robot4_motors.txt")
    logfile.read("robot4_scan.txt")

    # Also read the reference cylinders (this is our map).
    logfile.read("robot_arena_landmarks.txt")
    reference_cylinders = [l[1:3] for l in logfile.landmarks]

    if not os.path.exists("Generated_files"):
        os.makedirs("Generated_files")

    out_file = open("Generated_files/estimate_transform.txt", "w")
    for i in range(len(logfile.scan_data)):
        # Compute the new pose.
        pose = filter_step(pose, logfile.motor_ticks[i],
                           ticks_to_mm, robot_width,
                           scanner_displacement)

        # Extract cylinders, also convert them to world coordinates.
        cartesian_cylinders = compute_scanner_cylinders(
            logfile.scan_data[i],
            depth_jump, minimum_valid_distance, cylinder_offset)
        world_cylinders = [LegoLogfile.scanner_to_world(pose, c)
                           for c in cartesian_cylinders]

        # For every cylinder, find the closest reference cylinder.
        cylinder_pairs = find_cylinder_pairs(
            world_cylinders, reference_cylinders, max_cylinder_distance)

        # Estimate a transformation using the cylinder pairs.
        left_list = [world_cylinders[pair[0]] for pair in cylinder_pairs]
        right_list = [reference_cylinders[pair[1]] for pair in cylinder_pairs]
        trafo = estimate_transform(left_list,right_list,fix_scale = True)

        # Transform the cylinders using the estimated transform.
        transformed_world_cylinders = []
        if trafo:
            transformed_world_cylinders =\
                [apply_transform(trafo, c) for c in
                 [world_cylinders[pair[0]] for pair in cylinder_pairs]]            

        # Write to file.
        # The pose.
        out_file.write("F %f %f %f\n" % pose)
        # The detected cylinders in the scanner's coordinate system.
        write_cylinders(out_file, "D C", cartesian_cylinders)
        # The detected cylinders, transformed using the estimated trafo.
        write_cylinders(out_file, "W C", transformed_world_cylinders)

    out_file.close()
