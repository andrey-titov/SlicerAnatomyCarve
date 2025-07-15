import logging
import os
import time
from typing import Annotated, Optional

import vtk

from qt import QToolButton, QAbstractItemView

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode, vtkMRMLMarkupsFiducialNode, vtkMRMLMarkupsNode

try:
    from OpenGL.GL import *
except ImportError:
    slicer.util.pip_install('PyOpenGL')


from AnatomyCarveLogic import *
import numpy as np
from AnatomyCarveLogic.Texture import *
import vtkSegmentationCorePython as vtkSegmentationCore
from vtk.util import numpy_support
import qt


#
# AnatomyCarve
#


class AnatomyCarve(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("Anatomy Carve")
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Rendering")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Andrey Titov (Ecole de Technologie Superieure)" , "Liam O'Connor (Concordia University)"]
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
AnatomyCarve is a module that allows interactive visualization of 3D medical images by enabling users to perform clipping on segments of their choice. This customized carving of the dataset enables the creation of detailed visualizations similar to those found in anatomical textbooks.
See more information in <a href="https://github.com/andrey-titov/SlicerAnatomyCarve">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Andrey Titov, Ecole de Technologie Superieure and Liam O'Connor, Concordia University.
This work was funded by the Natural Sciences and Engineering Research Council of Canada, Discovery program (RGPIN-2020-05084), as well as by the Fonds de recherche du Quebec - Nature et technologies (B2X Doctoral Scholarship), Application 334501 (https://doi.org/10.69777/334501).
""")

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # AnatomyCarve1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="AnatomyCarve",
        sampleName="CTA abdomen (Panoramix) segmentation",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "Panoramix-cropped-segmentation.png"),
        # Download URL and target file name
        uris="https://raw.githubusercontent.com/andrey-titov/SlicerAnatomyCarve/main/data/Panoramix-cropped.seg.nrrd",
        fileNames="Panoramix-cropped.seg.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:327def5bb45f2ae86ce803aa5aa2b034f5d82dcc3eb3d0436eefd3bc09463ab8",
        # This node name will be used when the data set is loaded
        nodeNames="Panoramix-cropped_Segmentation",
    )




#
# AnatomyCarveWidget
#


class AnatomyCarveWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/AnatomyCarve.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = AnatomyCarveLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Buttons
        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)
        self.ui.renderButton.connect("clicked(bool)", self.onRenderButton)
        
        self.setupClippingSphereMarkups()

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()
        
    def setupClippingSphereMarkups(self):
        # assume you loaded your UI into self.ui
        clippingSpheres = self.ui.clippingSpheres  # qSlicerSimpleMarkupsWidget 

        # 1. Give it the MRML scene
        clippingSpheres.setMRMLScene(slicer.mrmlScene)

        # 2. Create (or grab) a fiducial node
        #node = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLMarkupsFiducialNode')
        #if not node:
        node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Clipping sphere")
        
        dispNode = node.GetDisplayNode()
        dispNode.SetSnapMode(slicer.vtkMRMLMarkupsDisplayNode.SnapModeUnconstrained)
        dispNode.SetOccludedVisibility(True)
        dispNode.SetOccludedOpacity(1.0)         # 1.0 = fully opaque when occluded        

        # 3. Tell the widget which node to display
        clippingSpheres.setCurrentNode(node)

        # 4. Enable “place” mode so clicks in the slice add points
        clippingSpheres.placeActive(False)
        
        table = clippingSpheres.tableWidget()
        table.setSelectionBehavior(qt.QAbstractItemView.SelectRows)
        table.setSelectionMode(qt.QAbstractItemView.SingleSelection)
        
        self.ui.clippingSpheres.currentMarkupsControlPointSelectionChanged.connect(self.onPointSelected)
        
        # node.AddObserver(vtkMRMLMarkupsNode.PointAddedEvent , self.onPointEvent)
        # node.AddObserver(vtkMRMLMarkupsNode.PointRemovedEvent , self.onPointEvent)
        # self._prevCount = node.GetNumberOfControlPoints()
        # clippingSpheres.updateFinished.connect(
        #     lambda: self.onMarkupsUpdated(node)
        # )
        
        # print(vtkMRMLMarkupsNode.PointAddedEvent)
        # print(vtkMRMLMarkupsNode.PointRemovedEvent)
        
        # proxy = MarkupChangeDetector(node)

        # # 3. Register your own add/remove handlers
        # proxy.onPointAdded(lambda idx, pos: print("Added at", idx, pos))
        # proxy.onPointRemoved(lambda idx, pos: print("Removed at", idx, pos))

        
        #node.AddObserver(vtkMRMLMarkupsNode.FixedNumberOfControlPointsModifiedEvent , self.onPointEvent)
        #node.AddControlPoint([0.0, 0.0, 0.0])
        
        node.AddObserver(vtkMRMLMarkupsNode.PointAddedEvent , self.onPointAddedEvent)
        # node.AddObserver(vtkMRMLMarkupsNode.PointAboutToBeRemovedEvent , self.onPointAboutToBeRemovedEvent)
        node.AddObserver(vtkMRMLMarkupsNode.PointRemovedEvent , self.onPointRemovedEvent)
        # widget = clippingSpheres
        
        # # 1) Disable the built‑in remove shortcut so it never does anything
        # try:
        #     widget.removeSelectedControlPoints.disconnect()
        # except Exception:
        #     pass

        # # 2) Reconnect it to our own slot
        # widget.removeSelectedControlPoints.connect(lambda: self._removeLastOnly(widget))

        # # 3) (Optional) grey‑out the remove button unless the last row is selected
        # removeBtn = None
        # for btn in widget.findChildren(QToolButton):
        #     if btn.toolTip().lower().startswith("remove"):
        #         removeBtn = btn
        #         break
        # if removeBtn:
        #     # selectionChanged gives you the newly selected row
        #     widget.currentMarkupsControlPointSelectionChanged.\
        #         connect(lambda idx: removeBtn.setEnabled(
        #         idx == widget.currentNode().GetNumberOfControlPoints()-1))

        # # also force the button state once at startup
        # if removeBtn:
        #     removeBtn.setEnabled(
        #         node.GetNumberOfControlPoints() <= 1)

    # def _removeLastOnly(self, widget):
    #     """
    #     Only actually remove a point if it’s the last one.
    #     (If the user selected any other row, do nothing.)
    #     """
    #     node = widget.currentNode()
    #     # get the selected row(s)
    #     sel = widget.tableWidget().selectionModel().selectedRows()
    #     if not sel:
    #         return
    #     idx = sel[0].row()
    #     last = node.GetNumberOfControlPoints() - 1
    #     if idx == last:
    #         node.RemoveNthControlPoint(idx)
    #     else:
    #         # optionally give feedback
    #         slicer.util.warningDisplay(
    #             "You can only remove the last point", windowTitle="Remove Point")

        

    # def onMarkupsUpdated(self, node):
    #     """
    #     Called whenever the widget’s list of control points has changed.
    #     Compare previous vs. current to see if points were added or removed.
    #     """
    #     currentCount = node.GetNumberOfControlPoints()
    #     if currentCount > self._prevCount:
    #         added = currentCount - self._prevCount
    #         slicer.util.infoDisplay(f"{added} point(s) added")
    #     elif currentCount < self._prevCount:
    #         removed = self._prevCount - currentCount
    #         slicer.util.infoDisplay(f"{removed} point(s) removed")
    #     # update your cache
    #     self._prevCount = currentCount

    def onPointAddedEvent(self, caller, eventId, callData=None):
        n = caller.GetNumberOfControlPoints()
        updatedPoints = [tuple(caller.GetNthControlPointPosition(i)) for i in range(n)]
        self.logic.addLastClippingSphere(updatedPoints)
        # n = slicer.util.getNode("Clipping sphere").GetNumberOfControlPoints()
        # print("onPointAddedEvent:", [tuple(slicer.util.getNode("Clipping sphere").GetNthControlPointPosition(i)) for i in range(n)])

    # def onPointAboutToBeRemovedEvent(self, caller, eventId, callData=None):
    #     n = slicer.util.getNode("Clipping sphere").GetNumberOfControlPoints()
    #     print("onPointAboutToBeRemovedEvent:", [tuple(slicer.util.getNode("Clipping sphere").GetNthControlPointPosition(i)) for i in range(n)])
        
    def onPointRemovedEvent(self, caller, eventId, callData=None):
        n = caller.GetNumberOfControlPoints()
        updatedPoints = [tuple(caller.GetNthControlPointPosition(i)) for i in range(n)]
        self.logic.removeLastClippingSphere(updatedPoints)
        # n = slicer.util.getNode("Clipping sphere").GetNumberOfControlPoints()
        # print("onPointRemovedEvent:", [tuple(slicer.util.getNode("Clipping sphere").GetNthControlPointPosition(i)) for i in range(n)])
        
    
    # def onPointEvent(self, caller, eventId, callData=None):
    #     # if callData is None you can fall back to e.g. GetNumberOfControlPoints()-1
    #     idx = int(callData) if callData is not None else None

    #     if eventId == vtkMRMLMarkupsNode.PointAddedEvent:
    #         print(f"Point added at index {idx}")
    #     elif eventId == vtkMRMLMarkupsNode.PointRemovedEvent:
    #         print(f"Point removed at index {idx}")
    #     else:
    #         # you’ll now see other event IDs (or 0 if something else is calling you)
    #         print("Other event:", eventId)
    #         n = slicer.util.getNode("Clipping sphere").GetNumberOfControlPoints()
    #         print("Resynced cache:", [tuple(slicer.util.getNode("Clipping sphere").GetNthControlPointPosition(i)) for i in range(n)])
            
        
    def onPointSelected(self, index):
        print(index)
        #slicer.util.getNode("Clipping sphere").AddObserver(vtkMRMLMarkupsNode.PointPositionDefinedEvent, self.onPointEvent)
    
    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode
        
        ## intensityVolume: load first
        #if not self._parameterNode.intensityVolume:
        #    firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
        #    if firstVolumeNode:
        #        self._parameterNode.intensityVolume = firstVolumeNode


    def setParameterNode(self, inputParameterNode: Optional[AnatomyCarveParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanRender)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanRender)
            self._checkCanApply()
            self._checkCanRender()

    def _checkCanApply(self, caller=None, event=None) -> None:
        if self._parameterNode and self._parameterNode.inputVolume and self._parameterNode.thresholdedVolume:
            self.ui.applyButton.toolTip = _("Compute output volume")
            self.ui.applyButton.enabled = True
        else:
            self.ui.applyButton.toolTip = _("Select input and output volume nodes")
            self.ui.applyButton.enabled = False

    def onApplyButton(self) -> None:
        """Run processing when user clicks "Apply" button."""
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            # Compute output
            self.logic.process(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(),
                               self.ui.imageThresholdSliderWidget.value, self.ui.invertOutputCheckBox.checked)

            # Compute inverted output (if needed)
            if self.ui.invertedOutputSelector.currentNode():
                # If additional output volume is selected then result with inverted threshold is written there
                self.logic.process(self.ui.inputSelector.currentNode(), self.ui.invertedOutputSelector.currentNode(),
                                   self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked, showResult=False)
                
    def _checkCanRender(self, caller=None, event=None) -> None:
        if self._parameterNode and self._parameterNode.intensityVolume and self._parameterNode.segmentation and self._parameterNode.view:
            self.ui.renderButton.toolTip = _("Start AnatomyCarve rendering")
            self.ui.renderButton.enabled = True
        else:
            self.ui.renderButton.toolTip = _("Select intesnsity volume, segmentation and view nodes")
            self.ui.renderButton.enabled = False

    def onRenderButton(self) -> None:
        """Run processing when user clicks "Apply" button."""
        with slicer.util.tryWithErrorDisplay(_("Failed to start rendering."), waitCursor=True):
            self.logic.startRender(self.ui.sphereRadius.value)



#
# AnatomyCarveTest
#


class AnatomyCarveTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_AnatomyCarve1()

    def test_AnatomyCarve1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData

        registerSampleData()
        inputVolume = SampleData.downloadSample("AnatomyCarve1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = AnatomyCarveLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")

# class MarkupChangeDetector:
#     """
#     Watches a vtkMRMLMarkupsFiducialNode and fires your own
#     onPointAdded/onPointRemoved callbacks when points really
#     appear or disappear (keys by control-point ID).
#     """
#     def __init__(self, node):
#         """
#         node: a vtkMRMLMarkupsFiducialNode (already added to the scene)
#         """
#         self.node = node
#         self._prevIds = self._gatherPointIds()
#         self._onAdded   = []
#         self._onRemoved = []
#         # Observe the generic ModifiedEvent on the node:
#         self._observerTag = node.AddObserver(
#             vtk.vtkCommand.ModifiedEvent, self._onModified)

#     def _gatherPointIds(self):
#         """Return list of (id, position) for each control point."""
#         ids = []
#         n = self.node.GetNumberOfControlPoints()
#         for i in range(n):
#             cpId = self.node.GetNthControlPointID(i)
#             pos = [0.0,0.0,0.0]
#             self.node.GetNthControlPointPosition(i, pos)
#             ids.append((cpId, tuple(pos)))
#         return ids

#     def _onModified(self, caller, eventId, callData=None):
#         """
#         Called on ANY modification: add, remove, or move.
#         We diff the list of IDs to find adds/removals.
#         """
#         current = self._gatherPointIds()
#         prev    = self._prevIds

#         prevIds = {cpId for cpId,_ in prev}
#         currIds = {cpId for cpId,_ in current}

#         addedIds   = currIds - prevIds
#         removedIds = prevIds - currIds

#         # Fire added callbacks
#         for cpId in addedIds:
#             # look up its index and position in the **current** list
#             for idx,(id_,pos) in enumerate(current):
#                 if id_ == cpId:
#                     for cb in self._onAdded:
#                         cb(idx, pos)
#                     break

#         # Fire removed callbacks
#         for cpId in removedIds:
#             # look up its index and position in the **previous** list
#             for idx,(id_,pos) in enumerate(prev):
#                 if id_ == cpId:
#                     for cb in self._onRemoved:
#                         cb(idx, pos)
#                     break

#         # update cache
#         self._prevIds = current

#     def onPointAdded(self, callback):
#         """
#         Register for “point added” events.
#         callback signature: f(index: int, position: tuple)
#         """
#         self._onAdded.append(callback)

#     def onPointRemoved(self, callback):
#         """
#         Register for “point removed” events.
#         callback signature: f(index: int, position: tuple)
#         """
#         self._onRemoved.append(callback)

#     def detach(self):
#         """If you ever want to stop observing."""
#         self.node.RemoveObserver(self._observerTag)