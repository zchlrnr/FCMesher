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

__title__ = 'FCMesher'
__author__ = '???'
__version__ = '0.1'
__license__ = 'LGPL v2+'
__date__    = '2021'

# temporary icons from oxygen LGPL v3+


import FreeCAD as App
import FreeCADGui as Gui


class FCMesher(Gui.Workbench):

    icon_path = App.getUserAppDataDir() + 'Mod/FCMesher/Resources/'
    MenuText = 'FCMesher'
    ToolTip = 'Tools to create meshes from enteties.'
    Icon = icon_path + 'applications-education.svg'

    def Initialize(self):
        """This function is executed when FreeCAD starts"""
        
        # import here all the needed files that create your FreeCAD commands
        import commands
        
        # A list of command names created in the
        self.list = commands.defined
        
        # creates a new toolbar with your commands
        self.appendToolbar('FCMesher', self.list)
        
        # creates a new menu
        self.appendMenu('FCMesher', self.list)
        # appends a submenu to an existing menu
        #self.appendMenu(["An existing Menu","My submenu"],self.list)

    def Activated(self):
        """This function is executed when the workbench is activated"""
        print('Loading FCMesher workbench.')
        return

    def Deactivated(self):
        """This function is executed when the workbench is deactivated"""
        return

    #def ContextMenu(self, recipient):
    #    """This is executed whenever the user right-clicks on screen"""
        
        # "recipient" will be either "view" or "tree"
        #self.appendContextMenu("My commands",self.list) # add commands to the context menu

    def GetClassName(self): 
        # This function is mandatory if this is a full python workbench
        # This is not a template,
        # the returned string should be exactly "Gui::PythonWorkbench"
        return "Gui::PythonWorkbench"
       
Gui.addWorkbench(FCMesher())
