import bpy
import sys
import os
import numpy as np
import random

dir = os.path.dirname(bpy.data.filepath)
dir = "/".join(dir.split("/")[:-2])
if not dir in sys.path:
    sys.path.append(dir)

# ------------------------------------------------------------------------------------ #
# Libs from github.com/islesarev317/Cellular-Automata-In-Blender
# ------------------------------------------------------------------------------------ #

from rule import CellRule
from virtual import VirtualObject, VirtualConstant, VirtualLife
from instance import Instance
from utils import catch_scene, clear_handlers, set_start_frame, show_label

# ------------------------------------------------------------------------------------ #
# 3D Cellular Automata in Blender. Basic cube.
# ------------------------------------------------------------------------------------ #

# preparing
set_start_frame()  # set current frame to 1

# params
frame_step = 10   # animation step
grain = 0.2  # size of each cell
scale_factor = 0.9  # to make gaps between cells
limit = 7000  # limit of cells for preventing overload
bake = True  # make animation keys for optimization
collection = bpy.data.collections["Cells"]  # collection to keep cells
image = bpy.data.objects["Image"]  # object to copy cell from
info = bpy.data.collections["Info"]  # collection for info labels

# rule
code_max = CellRule.get_max_code()  # rule 18014398509481983 always keeps each cell alive
code_flash = CellRule.get_flash_point()  # this and all codes greater result in uncontrolled growth
code_rand = CellRule.randrange(0, 100)  # random rule by range, 100 - flash point, 200 max point
code_maze = 8259390827203093  # some interesting rule
code_cond = CellRule.get_code(birth_cond=[4, 5, 6], survive_cond=[5, 6])  # from conditions
code_range = CellRule.get_code(birth_cond=list(range(4, 9)), survive_cond=[16, 26])  # from ranges

# info
msg_1 = "code_rand=" + str(code_rand)
msg_2 = "percent=" + str(CellRule.get_percent(code_rand))
show_label("1:", msg_1, collection=info)  # number of random rule
show_label("2:", msg_2, collection=info)  # percentage of random code relative to flash point

# objects
cube = VirtualObject(bpy.data.objects["Cube"], grain)

# expression
vf_init = cube.random_fill([0, 1], weights=[0.9, 0.1])  # create cube with random values
vf_init = vf_init.mirror()  # create symmetric matrix
vf_rule = cube.fill(code_maze)  # you can change code_maze to code_rand!
vf_life = VirtualLife(vf_rule, vf_init).hollow()  # create CA-function
 
# realize
instance = Instance(vf_life, grain, collection, image, bake, frame_step, limit)
instance.scale_factor = scale_factor
instance.label_collection = info
instance.update()

# handler
clear_handlers()
catch_scene(instance)
