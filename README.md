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
    - Two values for the number of elements along the curves, and between them
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
<table>
    <tr><th><b>Element</b></th><th><b> Element Type ID </b></th></tr>
    <tr><th>   CBAR       </th><th>            1           </th></tr>
    <tr><th>   CBUSH      </th><th>            2           </th></tr>
    <tr><th>   CELAS1     </th><th>            3           </th></tr>
    <tr><th>   CELAS2     </th><th>            4           </th></tr>
    <tr><th>   CELAS3     </th><th>            5           </th></tr>
    <tr><th>   CELAS4     </th><th>            6           </th></tr>
    <tr><th>   CHEXA      </th><th>            7           </th></tr>
    <tr><th>   CMASS1     </th><th>            8           </th></tr>
    <tr><th>   CMASS2     </th><th>            9           </th></tr>
    <tr><th>   CMASS3     </th><th>            10          </th></tr>
    <tr><th>   CMASS4     </th><th>            11          </th></tr>
    <tr><th>   CONM2      </th><th>            12          </th></tr>
    <tr><th>   CONROD     </th><th>            13          </th></tr>
    <tr><th>   CPENTA     </th><th>            14          </th></tr>
    <tr><th>   CQUAD4     </th><th>            15          </th></tr>
    <tr><th>   CQUAD4K    </th><th>            16          </th></tr>
    <tr><th>   CROD       </th><th>            17          </th></tr>
    <tr><th>   CSHEAR     </th><th>            18          </th></tr>
    <tr><th>   CTETRA     </th><th>            19          </th></tr>
    <tr><th>   CTRIA3     </th><th>            20          </th></tr>
    <tr><th>   CTRIA3K    </th><th>            21          </th></tr>
</table>

# P2T Specification
<table>
    <tr><th><b> Property </b></th><th><b> Property Type ID </b></th></tr>
    <tr><th>   [default]       </th><th>         0             </th></tr>
    <tr><th>     PELAS         </th><th>         1             </th></tr>
    <tr><th>     PBUSH         </th><th>         2             </th></tr>
    <tr><th>     PBAR          </th><th>         3             </th></tr>
    <tr><th>     PBARL         </th><th>         4             </th></tr>
    <tr><th>     PROD          </th><th>         5             </th></tr>
    <tr><th>     PSHEAR        </th><th>         6             </th></tr>
    <tr><th>     PCOMP         </th><th>         7             </th></tr>
    <tr><th>     PCOMP1        </th><th>         8             </th></tr>
    <tr><th>     PSOLID        </th><th>         9             </th></tr>
</table>

    * By default:
        - 1D elements will have a PBUSH property
        - 2D elements will have a PSHELL property
        - 3D elements will have a PSOLID property

# M2T Specification
<table>
    <tr><th><b>  Material  </b></th><th><b>Material Type ID</b></th></tr>
    <tr><th>   [default]       </th><th>         0             </th></tr>
    <tr><th>     MAT1          </th><th>         1             </th></tr>
    <tr><th>     MAT2          </th><th>         1             </th></tr>
    <tr><th>     MAT8          </th><th>         1             </th></tr>
    <tr><th>     MAT9          </th><th>         1             </th></tr>
    <tr><th>     PMASS         </th><th>         1             </th></tr>
</table>
