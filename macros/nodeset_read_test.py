# App = FreeCAD, Gui = FreeCADGui
import FreeCAD, Part, Fem
from PySide import QtGui
#from copy import copy as copy
#import math

def main(): # {{{
    """ See how we can get data out of these nodesets
    """
    nodeset_objects = []
    for obj in gui.selection.getselectionex():
        if obj.typename == "fem::femsetnodesobject":
            nodeset_objects.append(obj)

    if len(nodeset_objects) != 1:
        raise ValueError("as of 2021.10.17, only one nodeset may be selected.")

    # Let's see how we can get shit out of there.
    nodes_in_list = nodeset_objects[0].Object.Nodes
    for node in nodes_in_list:
        print(node)
# }}}

if __name__ == '__main__':
    main()
