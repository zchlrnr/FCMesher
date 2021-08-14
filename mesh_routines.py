# -*- coding: utf-8 -*-

# ***************************************************************************
# *   Copyright (c) 202x ?? <??@??.??>                                      *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************


"""
FCMesher
makes a ruled quad mesh.
"""

__title__ = 'FCMesher - mesh routines'
__author__ = '???'
__version__ = '0.1'
__license__ = 'LGPL v2+'
__date__    = '2021'

# temporary icons from oxygen LGPL v3+

import FreeCAD as App
import Fem
import Part

PrintMessage = App.Console.PrintMessage


def _points_fmt(seq):
    wrap = lambda it: '({})'.format(', '.join(it))
    return wrap((wrap(map('{:.1f}'.format, i)) for i in seq))

def fourpoint_warp(edge1, edge2):
    """endpoint lines with smallest distance reveals largest warp"""
    
    makeLine = Part.makeLine
    
    e11, e12 = edge1.discretize(2) # gives App.Vector
    e21, e22 = edge2.discretize(2)
        
    pairs = ((e11, e21), (e11, e22), (e12, e21), (e12, e22))
    l11, l12, l21, l22 = (makeLine(*pair) for pair in pairs)
    
    dii, *_ = l11.distToShape(l22)
    dij, *_ = l12.distToShape(l21)
    
    ## debug orientation, for no good, since it does not appear to be
    ## deterministic for edge orientation from fc point of view
#    print('-'*10)
#    print(edge1.Orientation, edge2.Orientation)
#    print(_points_fmt((tuple(v) for v in edge2.discretize(2))))
    
#    Part.show(l11); Part.show(l22) # draws ii lines
#    print('dii, dij:', dii, dij, dii < dij)
#    print(sum(l.Length for l in (l11, l22)), sum(l.Length for l in (l12, l21)))
    # suppose one could work with edge lengths as well

    return dii < dij


def make_mesh_from_edges(sel_edges, N_elms_X, N_elms_Y, force_flip=False):
    """returns fc mesh object and a bool for 2nd edge flip"""

    edge01, edge02 = sel_edges

    # get the nodes on curve_01
    N_Curve_1 = get_nodes_from_curve(edge01, N_elms_X)

    # get the nodes on curve_02
    N_Curve_2 = get_nodes_from_curve(edge02, N_elms_X)
    

    flipped = False
    if len(edge01.Vertexes + edge02.Vertexes) == 4:
        # check if curve 2 should be reversed
        # use the fact that an edge has two vertexes
    
        if fourpoint_warp(edge01, edge02):
            PrintMessage('Second curve is flipped, correcting...\n')
            N_Curve_2 = N_Curve_2[::-1]
            flipped = not flipped
            
        if force_flip:
            PrintMessage('Second curve is force flipped...\n')
            N_Curve_2 = N_Curve_2[::-1]
            flipped = not flipped
    else:
        pass
        # a circle or circle like has one vertex, no need for flipping
        
    
    # Make nodes by tracing the streamlines of the surface
    nodes = make_nodes_of_ruled_mesh(N_Curve_1, N_Curve_2, N_elms_Y)
    
    # Now to make the elements
    E2N = make_elements_of_ruled_mesh(N_elms_X, N_elms_Y)
    
    # Now have E2N and Nodes array
    # Add all of the nodes to a container called 'mesh'
    mesh = Fem.FemMesh()

    # add all of the nodes to mesh object
    for node in nodes:
        mesh.addNode(*node)
    # add all of the elements to mesh object
    for E in E2N:
        #print(E)
        mesh.addFace(E[1:], E[0])

    return mesh, flipped


def make_elements_of_ruled_mesh(N_elms_X, N_elms_Y):
    Nx = N_elms_X + 1
    Ny = N_elms_Y + 1
    EID = 0
    E2N = []
    for j in range(Ny):
        for i in range(Nx):
            NID = 1 + Nx*j + i
            # skip rolling over elements
            if i == (Nx - 1) or j == (Ny - 1):
                continue
            EID += 1
            N1 = NID
            N2 = 1 + Nx*(j+1) + i
            N3 = N2 + 1
            N4 = N1 + 1
            E2N.append([EID, N1, N2, N3, N4])
    return E2N

def get_nodes_from_curve(Curve_Handle, N_elms):
    return tuple((n.x, n.y, n.z) for n in Curve_Handle.discretize(N_elms+1))

def make_nodes_of_ruled_mesh(Nodes_1, Nodes_2, N_elms_Y):
    # Make nodes by tracing the streamlines of the surface
    nodes = []
    # first set of nodes will be from N_Curve_1
    NID = 0
    for i in range(N_elms_Y+1):
        for j in range(len(Nodes_1)):
            NID += 1
            # Get coordinates of the node on Curve 1
            x1, y1, z1 = Nodes_1[j]
            # Get coordinates of the node on Curve 2
            x2, y2, z2 = Nodes_2[j]
            # get location of current node in ruled surf
            x = (x2-x1)*(i/N_elms_Y) + x1
            y = (y2-y1)*(i/N_elms_Y) + y1
            z = (z2-z1)*(i/N_elms_Y) + z1
            nodes.append([x, y, z, NID])
    return nodes
