FCMesher
========

FCMesher is a toolset for orphan mesh creation and manipulation.

---

[Shell_mesh_loft_between_two_curves](#shell_mesh_loft_between_two_curve) |
[Solid_mesh_by_thickened_shell_mesh](#solid_mesh_by_thickened_shell_mesh)

---

# Shell_mesh_loft_between_two_curves

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

# Solid_mesh_by_thickened_shell_mesh

* Inputs:
    - Elementary shell mesh data structures and the thickness
    - nodes[NID] = [X_coordinte, Y_coordinate, Z_coordinate]
    - E2N[EID] = [NID1, NID2, NID3, NID4]
    - E2T[EID] = [TypeID] 
    - thickness
* Outputs:
    - Elementary solid mesh data structures
    - nodes[NID] = [X_coordinte, Y_coordinate, Z_coordinate]
    - E2N_offset[EID] = [NID1, NID2, NID3, NID4]
    - E2T_offset[EID] = [TypeID] 
# E2T Specification

| E2T Specification |
| :------: | :----: |
|  CBAR    |   1    |
|  CBUSH   |   2    |
|  CELAS1  |   3    |
|  CELAS2  |   4    |
|  CELAS3  |   5    |
|  CELAS4  |   6    |
|  CHEXA   |   7    |
|  CMASS1  |   8    |
|  CMASS2  |   9    |
|  CMASS3  |   10   |
|  CMASS4  |   11   |
|  CONM2   |   12   |
|  CONROD  |   13   |
|  CPENTA  |   14   |
|  CQUAD4  |   15   |
|  CQUAD4K |   16   |
|  CROD    |   17   |
|  CHEAR   |   18   |
|  CTETRA  |   19   |
|  CTRIA3  |   20   |
|  CTRIA3K |   21   |
