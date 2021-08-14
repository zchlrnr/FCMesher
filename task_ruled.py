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

__title__ = 'FCMesher - taskpanel'
__author__ = '???'
__version__ = '0.1'
__license__ = 'LGPL v2+'
__date__    = '2021'

# temporary icons from oxygen LGPL v3+

from collections import deque, namedtuple

import FreeCAD as App
import FreeCADGui as Gui
import Part

from mesh_routines import make_mesh_from_edges

from PySide import QtCore, QtGui, QtSvg

QDock, QTree = QtGui.QDockWidget, QtGui.QTreeWidget

PrintMessage = App.Console.PrintMessage
icon_path = App.getUserAppDataDir() + 'Mod/FCMesher/Resources/'

Selection = namedtuple('Selection', 'object entity')

HighLight = (1., 0., 1., 0.) # color


class Gate:
    
    def allow(self, doc, obj, sub):
        """evaluates pre-selection in 3d view"""
#        print('==gate', doc.Name, obj.Name, sub)
        return 'Edge' in sub


class SelectionObserver:
    """fires on changes in selection, married with this task panel"""
    que = deque(list(), 2)
    tp = None

    def addSelection(self, document, obj, element, position):
        """Added single object to selection"""
#        PrintMessage('**addSelection\n')
#        PrintMessage('  {} : {}\n'.format(obj, element))
        
        if element:
            self.que.append(Selection(obj, element))
        
        self.tp.update_presentation()

    def removeSelection(self, document, obj, element):
        """Removed single object from selection."""
#        PrintMessage('**removeSelection\n')
#        PrintMessage('  {} : {}\n'.format(obj, element))

        # need to check if obj/elem is in que and remove it
        if self.que and document == App.ActiveDocument.Name:
            try:
                self.que.remove(Selection(obj, element))
            except ValueError as e:
                pass

        self.tp.update_presentation()
                    

    def _singleEdge(self, document, obj):
        objh = App.getDocument(document).getObject(obj)
        if hasattr(objh, 'Shape'):
            edges = objh.Shape.Edges
            if len(edges) == 1:
                return True

    def _initial_selection(self):
        """gather any edges from selection when entering command"""
        for selobj in Gui.Selection.getSelectionEx():
            if selobj.DocumentName == App.ActiveDocument.Name:
#                print('initial sel - subobjnames', selobj.SubElementNames)
                objname = selobj.ObjectName
                for entity in selobj.SubElementNames:
                    if 'Edge' in entity:
                        self.que.append(Selection(objname, entity))
                # could be a treeview selection holding a single edge
                if self._singleEdge(selobj.DocumentName, objname):
                    # can already be there pending specific click history
                    candidate = Selection(objname, 'Edge1')
                    if not candidate in self.que:
                        self.que.append(candidate)

        self.tp.update_presentation()


def busy(function):
    """boiler to set wait cursor on gui"""
    def new_func(self, *args, **kwargs):
        waitcursor = QtGui.QCursor(QtCore.Qt.WaitCursor)
        QtGui.QApplication.setOverrideCursor(waitcursor)
        try:
            function(self, *args, **kwargs)
        except Exception as e:
            pass
        finally:
            QtGui.QApplication.restoreOverrideCursor()
    return new_func


class TaskPanel:
    """task panel for 2 edges"""
    N_elms_X = 5
    N_elms_Y = 3
    _original_colors = dict()
    
    def __init__(self):
        PrintMessage('Ruled Surface mesh...\n')
        mw = self.mw = Gui.getMainWindow()
        self.form = mw.findChild(QtGui.QWidget, 'TaskPanel')
        self._selection_icons = self._load_spics()
        self.makeUI()
        
        self.selobjs = s = SelectionObserver()
        s.tp = self
        s._initial_selection()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelectionGate(Gate())
        Gui.Selection.addObserver(s)
        

    def makeUI(self):
        """"""
        
        upperframe = QtGui.QGroupBox('Selection')
        
        clear_sel = QtGui.QPushButton('Clear Selection')
        clear_sel.clicked.connect(self._clear_selection)
        
        labeled1 = QtGui.QLabel('Selected Edge #1')
        piced1 = self._pic1 = QtGui.QLabel()
        piced1.setPixmap(self._selection_icons['red'])
        labelsel1 = self._lsel1 = QtGui.QLabel('')
        
        labeled2 = QtGui.QLabel('Selected Edge #2')
        piced2 = self._pic2 = QtGui.QLabel()
        piced2.setPixmap(self._selection_icons['red'])
        labelsel2 = self._lsel2 = QtGui.QLabel('')
        
        selgrid = self._sg = QtGui.QGridLayout()
        selgrid.addWidget(clear_sel, 0, 1)
        ac = QtCore.Qt.AlignCenter
        for args in ((labeled1, 1, 0), (piced1, 1, 1, ac), (labelsel1, 1, 2),
                     (labeled2, 2, 0), (piced2, 2, 1, ac), (labelsel2, 2, 2)):
            selgrid.addWidget(*args)
        
        upperframe.setLayout(selgrid)
        
        
        labelx = QtGui.QLabel('X - direction:')
        spinx = self.spinx = QtGui.QSpinBox()
        spinx.setValue(self.N_elms_X)
        spinx.setRange(2, 100)
        
        labely = QtGui.QLabel('Y - direction:')
        spiny = self.spiny = QtGui.QSpinBox()
        spiny.setValue(self.N_elms_Y)
        spiny.setRange(2, 100)
        
        nbrgrid = QtGui.QGridLayout()
        for w, r, c in ((labelx, 0, 0), (spinx, 0, 1),
                        (labely, 1, 0), (spiny, 1, 1)):
            nbrgrid.addWidget(w, r, c)
        
        lowerframe = QtGui.QGroupBox('Number of elements')
        lowerframe.setLayout(nbrgrid)
        
        txt = 'Force flip 2nd edge for mesh and surface.'
        checkboxff = self.cbff = QtGui.QCheckBox(txt)
        checkboxrs = self.cbrs = QtGui.QCheckBox('Make surface.')
        checkboxrs.setCheckState(QtCore.Qt.CheckState.Checked)
        txt = 'Force flip of orientationf for 2nd edge for surface.'
        checkboxsff = self.cbsff = QtGui.QCheckBox(txt)

        frame = QtGui.QWidget(objectName='TaskPanel')
        vbox = QtGui.QVBoxLayout()
        for w in (upperframe, lowerframe, checkboxff, checkboxrs, checkboxsff):
            vbox.addWidget(w)
        frame.setLayout(vbox)
        
        self.form = frame

    def _get_edge(self, doc, objname, edgeid):
        return getattr(doc.getObject(objname).Shape, edgeid)

    @busy
    def accept(self):
        """triggered by ok click"""
        PrintMessage('++ meshing...\n')
        doc = App.ActiveDocument
        edges = [self._get_edge(doc, ed.object, ed.entity)
                 for ed in self.selobjs.que]
        arguments = (edges, self.spinx.value(), self.spiny.value(),
                     self.cbff.isChecked())
        
        meshsurf, flipped = make_mesh_from_edges(*arguments)

        # Add to doc and making it render correctly
        obj = doc.addObject('Fem::FemMeshObject', 'RuledMesh')
        obj.FemMesh = meshsurf
        obj.Placement.Base = App.Vector(0, 0, 0)
        obj.ViewObject.DisplayMode = 'Faces, Wireframe & Nodes'
        obj.ViewObject.BackfaceCulling = False

        if self.cbrs.isChecked():
            ed1, ed2 = edges

            if ed1.Orientation != ed2.Orientation:
                PrintMessage('Edges have different orientation, '
                             'aligning for surface only.\n')
                ed2.Orientation = ed1.Orientation

            if flipped:
                ed2 = ed2.reversed()
            
            # no clear way to determine correct orientation for ruled surface
            # edge.Orientation does not influence actual order of any of
            # .Vertexes, .discretize or .firstVertex are returned
            # fallback is user option to force orientation just for surface
            # before creation if the recognition algo fails
            if self.cbsff.isChecked():
                ed2 = ed2.reversed()
                PrintMessage('Second curve is force flipped for surface...\n')
                
            ruled = Part.makeRuledSurface(ed1, ed2)
            Part.show(ruled, 'RuledSurface')
        
        doc.recompute()
        PrintMessage('-- done...\n')
        
        return True

    def reject(self):
        """triggered by cancel or close click"""
        Gui.Selection.removeObserver(self.selobjs)
        Gui.Selection.removeSelectionGate()
        self.selobjs.que.clear()
        self.update_presentation()
        PrintMessage('Exiting ruled mesh command.\n')

        return True
    
    def clicked(self, index):
        """fires with any button click"""
        if index == int(QtGui.QDialogButtonBox.Apply):
            if len(self.selobjs.que) == 2:
                self.accept()

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close)


    def _load_spics(self):
        icos = dict()
        for ico in ('red', 'green'):
            svg_renderer = QtSvg.QSvgRenderer(icon_path + f'flag-{ico}.svg')
            image = QtGui.QImage(32, 32, QtGui.QImage.Format_ARGB32)
            image.fill(0x00000000)
            svg_renderer.render(QtGui.QPainter(image))
            icos[ico] = QtGui.QPixmap.fromImage(image)
        
        return icos

    def _clear_selection(self):
        Gui.Selection.clearSelection()
        self.selobjs.que.clear()
        self.update_presentation()


    def _store_object_color(self, objname):
        if not objname in self._original_colors:
            obj = App.ActiveDocument.getObject(objname)
            color = obj.ViewObject.LineColor
            self._original_colors.update({objname: color})
            if len(obj.ViewObject.LineColorArray) != len(obj.Shape.Edges):
                obj.ViewObject.LineColorArray = [color] * len(obj.Shape.Edges)
                
    def _restore_colors(self):
        for objname, color in self._original_colors.items():
            obj = App.ActiveDocument.getObject(objname)
            obj.ViewObject.LineColorArray = [color] * len(obj.Shape.Edges)
            
    def update_presentation(self):
        """renders selection status"""
        que = self.selobjs.que
#        print('updating', que)
        lbl1, lbl2 = self._lsel1, self._lsel2
        pic1, pic2 = self._pic1, self._pic2
        green = self._selection_icons['green']
        red = self._selection_icons['red']
        fmt = '{}.{}'
        for objname, _ in que:
            self._store_object_color(objname)
            
        if len(que) == 0:
            pic1.setPixmap(red); pic2.setPixmap(red)
            lbl1.setText(''); lbl2.setText('')
        elif len(que) == 1:
            ed1, = que
            pic1.setPixmap(green); pic2.setPixmap(red)
            lbl1.setText(fmt.format(*ed1)); lbl2.setText('')
        elif len(que) == 2:
            ed1, ed2 = que
            pic1.setPixmap(green); pic2.setPixmap(green)
            lbl1.setText(fmt.format(*ed1)); lbl2.setText(fmt.format(*ed2))
            
        self._restore_colors()

        # do the highlight
        get_edgeidx = lambda s: int(s.replace('Edge', ''))
        for objname, entity in que:
            obj = App.ActiveDocument.getObject(objname)
            colors = obj.ViewObject.LineColorArray
            edgeidx = get_edgeidx(entity)
            colors[edgeidx-1] = HighLight
            obj.ViewObject.LineColorArray = colors
            
        Gui.Selection.clearSelection()
