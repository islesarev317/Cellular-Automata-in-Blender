import bpy
import sys
import os

dir = os.path.dirname(bpy.data.filepath)
if not dir in sys.path:
    sys.path.append(dir)

import tensor
import utils
import realize_dynamic
import obj_to_tensor
import virtual_object
import virtual_function

import imp

imp.reload(tensor)
imp.reload(utils)
imp.reload(realize_dynamic)
imp.reload(obj_to_tensor)
imp.reload(virtual_object)
imp.reload(virtual_function)

from tensor import LocatedTensor
from utils import print
from realize_dynamic import InstanceDynamic
from obj_to_tensor import obj_to_tensor
from virtual_object import VirtualObject
from virtual_function import VirtualFunction

# ==================================================

# params

grain = 0.5
collection = bpy.data.collections["Collection"]
default_image = bpy.data.objects["Cell"]

# objects

a = VirtualObject(bpy.data.objects["Cube"], grain)
b = VirtualObject(bpy.data.objects["Ico"], grain)

# virtual

virtual_function = (a + b).hollow()

# realize

instance = InstanceDynamic(grain, collection, default_image)

# update

tensor = virtual_function.compute()
instance.update(tensor)
