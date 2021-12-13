# App = FreeCAD, Gui = FreeCADGui
from typing import Tuple, List, Dict
import FreeCAD, Part, Fem
Vector = App.Vector

def main(): # {{{
    # get nodelist that's clicked on
    node_set_entities = []
    for obj in Gui.Selection.getSelectionEx():
        if obj.TypeName == "Fem::FemSetNodesObject":
            node_set_entities.append(obj)

    if len(node_set_entities) > 1:
        raise ValueError("Too many node sets selected.")
    elif len(node_set_entities) == 0:
        raise ValueError("No node sets selected")

    # need to get the label of the mesh entity that's associated
    fem_mesh_name = node_set_entities[0].Object.FemMesh.Label

    # searching active doc for the mesh set linked label
    mesh_object = App.ActiveDocument.getObjectsByLabel(fem_mesh_name)
    if len(mesh_object) != 1:
        err_string = "More than one mesh object called " + fem_mesh_name
        raise ValueError(err_string)
    mesh_object = mesh_object[0].FemMesh

    # get the node IDs that I care about
    node_IDs = obj.Object.Nodes

    # compute "nodes" of the mesh entity
    nodes = {}
    for NID in node_IDs:
        nodes[NID] = list(mesh_object.Nodes[NID])

    # get the location of the central node of the spider
    x_bar, y_bar, z_bar = get_centroid_from_nodes(nodes)

    # get highest NID in original mesh object
    NID_center = len(mesh_object.Nodes) + 1

    # create a new mesh entity for the bush spider
    bush_spider = Fem.FemMesh()
    # make a grid point, at the centeral location
    bush_spider.addNode(x_bar, y_bar, z_bar, NID_center)
    # add nodes, and make seg2 elements to the
    for NID, node in nodes.items():
        node[0]
        bush_spider.addNode(node[0], node[1], node[2], NID)
        bush_spider.addEdge(NID, NID_center)
    print(f'bush_spider = {bush_spider}')

    # Making it render correctly
    doc = App.ActiveDocument
    obj = doc.addObject("Fem::FemMeshObject", "bush_spider")
    obj.FemMesh = bush_spider
    obj.Placement.Base = FreeCAD.Vector(0, 0, 0)
    obj.ViewObject.DisplayMode = "Faces, Wireframe & Nodes"
    obj.ViewObject.BackfaceCulling = False
    doc.recompute()
# }}}

def get_centroid_from_nodes(nodes: Dict[int, List[float]]) -> Tuple[float, float, float]: # {{{
    x_bar = 0.
    y_bar = 0.
    z_bar = 0.
    for xyz in nodes.values():
        x_bar += xyz[0]
        y_bar += xyz[1]
        z_bar += xyz[2]
    nnodes = len(nodes)
    x_bar /= nnodes
    y_bar /= nnodes
    z_bar /= nnodes
    return x_bar, y_bar, z_bar
# }}}
if __name__ == '__main__':
    main()
