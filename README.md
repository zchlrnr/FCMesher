## FCMesher

A toolset for orphan mesh creation and manipulation in FreeCAD, with the
secondary goal of creating include file generation procedures for
mystran/nastran.

Assistance in making gui elements would be very greatly appreciated.

Macros should be listed in order of descending usefulness in this authors
opinion.

### Macros

#### export_mesh_as_bdf.py
* Exports selcted FemMeshObject(s) and/or FemMeshObjectPython(s) to a nastran bulk
  data file. The only way to actually export multiple parts in a single
  analysis, to this authors knowledge.

#### export_nodeset.py
* Exports selected nodesets and uses the nodeset labels to create
  appropriate include files for single point constraints and forces.
* The two formats for labels current supported are
    - SPC: "NAME: SPC1_SID_C"
    - Force: "NAME: FORCE_SID_Scale_Vx_Vy_Vz"

#### flip_shell_mesh_normals.py
* flips the normals of a shell mesh entity by reversing the node order

#### proto_mesh_equivalencer.py
* Collapses two FemMeshObjects together into a single one by replacing nodes
  within a small tolerance with the nearest one in the other body, and globally
  renumbering the nodes and elements.
* Goal is to replace this with something that can maintain the original meshes
  and only renumber the nodes to be common, such that a secondary pass of
  removing duplicate GRID lines in the bdf will be able to effectively crush the
  two together. Work on that is stalled until I can figure out who in their
  right mind would EVER think that wanton disregard for IDs, and arbitrary
  renumbering of nodes and elements was a good idea; and then how I can stop
  their terrible ideas from destroying my meshes. 

#### proto_shell_mesh_with_FC_gui.py
* makes a ruled shell mesh as a ruled mesh between two curves

### Solid mesh by thickened shell mesh

* Inputs:
    - Elementary shell mesh data structures and the thickness
    - `nodes[NID] = [X_coordinte, Y_coordinate, Z_coordinate]`
    - `E2N[EID] = [NID1, NID2, NID3, NID4]`
    - `E2T[EID] = [TypeID]`
    - thickness
* Outputs:
    - Elementary solid mesh data structures
    - `nodes[NID] = [X_coordinte, Y_coordinate, Z_coordinate]`
    - `E2N_offset[EID] = [NID1, NID2, NID3, NID4]`
    - `E2T_offset[EID] = [TypeID]`

## E2T Specification
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

## P2T Specification
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

## M2T Specification
<table>
    <tr><th><b>  Material  </b></th><th><b>Material Type ID</b></th></tr>
    <tr><th>   [default]       </th><th>         0             </th></tr>
    <tr><th>     MAT1          </th><th>         1             </th></tr>
    <tr><th>     MAT2          </th><th>         2             </th></tr>
    <tr><th>     MAT8          </th><th>         3             </th></tr>
    <tr><th>     MAT9          </th><th>         4             </th></tr>
    <tr><th>     PMASS         </th><th>         5             </th></tr>

    * By default:
        - 1D elements will have no material property
        - 2D elements will have a MAT1 property
        - 3D elements will have a MAT1 property
</table>
