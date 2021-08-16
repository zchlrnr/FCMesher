import re
import math as m
import numpy as np
from mesh_utilities import *

# Hard coded Values
# -----------------
# hard code thickness by which to sweep the quads into hexes
thickness = 0.125
# make three points, defining a line 1
L1 = [[0.0, 0.0, 0.0], [1.0, 0.5, 0.0], [2.0, 0.0, 0.0]]
# make three points, defining a line 2
L2 = [[0.0, 0.0, 3.0], [1.0, 1.0, 3.0], [2.0, 0.0, 3.0]]
# There's elements along the curve X, and elements between the curves Y
Number_of_elements_along_X = 42
Number_of_elements_along_Y = 42

# Helper code to make the points along the curves
# -----------------------------------------------
# get the nodes on Line 1
points_on_L1 = get_points_on_3_point_quadratic_fit(\
        Number_of_elements_along_X, L1)
# get the nodes on Line 2
points_on_L2 = get_points_on_3_point_quadratic_fit(\
        Number_of_elements_along_Y, L2)

# Calling the star of the show
# ============================
[nodes, E2N, E2T] = shell_mesh_loft_between_two_curves(points_on_L1,\
        points_on_L2, Number_of_elements_along_X, Number_of_elements_along_Y)

argument_stack = [thickness, nodes, E2N, E2T]
data_back = solid_mesh_by_thickened_shell_mesh(argument_stack)
