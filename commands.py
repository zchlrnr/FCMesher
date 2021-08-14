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

__title__ = 'FCMesher - commands'
__author__ = '???'
__version__ = '0.1'
__license__ = 'LGPL v2+'
__date__    = '2021'

# temporary icons from oxygen LGPL v3+


import FreeCAD as App
import FreeCADGui as Gui

from task_ruled import TaskPanel

icon_path = App.getUserAppDataDir() + 'Mod/FCMesher/Resources/'

defined = ['RuledMesh']

class RuledMesh():
    """the ruled quad mesh"""

    def GetResources(self):
        return {'Pixmap'  : icon_path + 'roll.svg',
                #'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': 'Ruled Mesh',
                'ToolTip' : 'Ruled Quad mesh from 2 edges.'}

    def Activated(self):
        """command has been triggered"""
        panel = TaskPanel()
        Gui.Control.showDialog(panel)        
        return

    def IsActive(self):
        """
        Here you can define if the command must be active or not (greyed)
        if certain conditions are met or not. This function is optional.
        """
        return True

Gui.addCommand('RuledMesh', RuledMesh())
