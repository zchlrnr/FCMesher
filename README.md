FCMesher
========

FCMesher is a toolset for orphan mesh creation and manipulation.

---

[shell_mesh_loft_between_two_curves](###shell_mesh_loft_between_two_curves.py) |
[solid mesh creation from shell mesh](###solid_mesh_by_thickened_shell_mesh.py)

---

### shell_mesh_loft_between_two_curves
* Inputs:
    - Two lists of point locations representing two curves
    - L1 = [[x1L1, y1L1, z1L1],[x2L1, y2L1, z2L1],...[xnL1, ynL1, znL1]]
    - L2 = [[x1L2, y1L2, z1L2],[x2L2, y2L2, z2L2],...[xnL2, ynL2, znL2]]
* Outputs:
    - Elementary data structures needed to characterize the 
    - nodes[NID] = [X_coordinte, Y_coordinate, Z_coordinate]
    - E2N[EID] = [NID1, NID2, NID3, NID4]
    - E2T[EID] = [TypeID] 
        - For a CQUAD4, the element type is 15

### solid_mesh_by_thickened_shell_mesh
* Inputs:
    - Elementary 
* Outputs:
