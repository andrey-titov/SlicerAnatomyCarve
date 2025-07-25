import logging
import os
import time
from typing import Annotated, Optional

import vtk

from qt import Qt, QEvent, QAbstractItemView

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
        # self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)
        self.ui.renderButton.connect("clicked(bool)", self.onRenderButton)
        
        self.ui.sphereRadius.connect('valueChanged(double)', self.onSphereRadiusValueChanged)
        
        #self.setupClippingSphereMarkups()

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
        node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Clipping Spheres")
        node.SetMarkupLabelFormat("S-%02d")
        self.clippingSpheresNode = node
        
        dispNode = node.GetDisplayNode()
        dispNode.SetSnapMode(slicer.vtkMRMLMarkupsDisplayNode.SnapModeUnconstrained)
        dispNode.SetOccludedVisibility(True)
        dispNode.SetOccludedOpacity(1.0)         # 1.0 = fully opaque when occluded        

        # 3. Tell the widget which node to display
        clippingSpheres.setCurrentNode(node)

        # 4. Enable “place” mode so clicks in the slice add points
        clippingSpheres.placeActive(False)
        
        table = clippingSpheres.tableWidget()
        
        ## Should be added when random removal/moving of the points is implemented
        # table.setSelectionBehavior(qt.QAbstractItemView.SelectRows)
        # table.setSelectionMode(qt.QAbstractItemView.SingleSelection)
        
        # Easier aleternative
        # table.setSelectionMode(QAbstractItemView.NoSelection)
        # table.setFocusPolicy(Qt.NoFocus)
        # table.setContextMenuPolicy(Qt.NoContextMenu)
        # table.viewport().setContextMenuPolicy(Qt.NoContextMenu)
        
        w = self.ui.clippingSpheres

        for btn in w.findChildren(qt.QToolButton):
            # toolTip is a str property, not a callable
            tip = btn.toolTip
            if not tip:
                continue
            if any(keyword in tip.lower() for keyword in (
                    "delete", "remove", "unset", "move up", "move down")):
                btn.hide()

        # 2) Steal the table view (fallback from QTableView → QAbstractItemView)
        tv = w.findChild(qt.QTableView)
        if not tv:
            tv = w.findChild(qt.QAbstractItemView)

        # 3) Disable any reordering and context‑menu deletion…
        if tv:
            tv.setDragEnabled(False)
            tv.setAcceptDrops(False)
            tv.setDragDropMode(qt.QAbstractItemView.NoDragDrop)
            tv.setContextMenuPolicy(qt.Qt.NoContextMenu)

            # 4) …but keep normal click‑to‑select
            tv.setSelectionBehavior(qt.QAbstractItemView.SelectRows)
            tv.setSelectionMode(qt.QAbstractItemView.SingleSelection)
        
        self.ui.clippingSpheres.currentMarkupsControlPointSelectionChanged.connect(self.onPointSelected)
        
                
        self.tagPointAddedEvent = node.AddObserver(vtkMRMLMarkupsNode.PointAddedEvent , self.onPointAddedEvent)
        self.tagPointRemovedEvent = node.AddObserver(vtkMRMLMarkupsNode.PointRemovedEvent , self.onPointRemovedEvent)

    def onPointAddedEvent(self, caller, eventId, callData=None):
        # Clear error from event
        err = glGetError()

        # n = caller.GetNumberOfControlPoints()
        # updatedPoints = [tuple(caller.GetNthControlPointPosition(i)) for i in range(n)]
        selectedSphereIndex = self.logic.addLastClippingSphere(self.ui.sphereRadius.value)
        self.selectRow(selectedSphereIndex)
        # n = slicer.util.getNode("Clipping sphere").GetNumberOfControlPoints()
        #print("onPointAddedEvent:", [tuple(slicer.util.getNode("Clipping sphere").GetNthControlPointID(i)) for i in range(n)])
        
        
    def onPointRemovedEvent(self, caller, eventId, callData=None):
        # Clear error from event
        err = glGetError()

        # n = caller.GetNumberOfControlPoints()
        # updatedPoints = [tuple(caller.GetNthControlPointPosition(i)) for i in range(n)]
        selectedSphereIndex, previousSphereRadius = self.logic.removeLastClippingSphere()
        
        self.selectRow(selectedSphereIndex)
        
        if previousSphereRadius is not None:
            self.ui.sphereRadius.setValue(previousSphereRadius)
        # n = slicer.util.getNode("Clipping sphere").GetNumberOfControlPoints()
        # print("onPointRemovedEvent:", [tuple(slicer.util.getNode("Clipping sphere").GetNthControlPointPosition(i)) for i in range(n)])
            
        
    def onPointSelected(self, index):
        # Clear error from event
        err = glGetError()

        #pass
        #print(index)
        newSphereRadius = self.logic.changeSelctedPointIndex(index)
        #self.selectRow(selectedSphereIndex)
        
        self.ui.sphereRadius.setValue(newSphereRadius)
        #slicer.util.getNode("Clipping sphere").AddObserver(vtkMRMLMarkupsNode.PointPositionDefinedEvent, self.onPointEvent)
    
    def onSphereRadiusValueChanged(self, newSphereRadius: float):
        # Clear error from event
        err = glGetError()

        self.logic.updateClippingSphereRadius(newSphereRadius)        
        
    def selectRow(self, row: int):
        
        if row == -1:
            return
        
        w = self.ui.clippingSpheres

        # 1) grab the internal QTableView
        tv = w.findChild(qt.QTableView)
        if not tv:
            raise RuntimeError("Couldn’t find the table view inside the simpleMarkupsWidget")

        # 2) clear any old selection
        tv.clearSelection()

        # 3) pick the row you want (zero‑based)
        #row = 0

        # 4) highlight that entire row
        tv.selectRow(row)

        # 5) optionally move keyboard focus/current index there
        idx = tv.model().index(row, 0)
        tv.setCurrentIndex(idx)

        # 6) scroll it into view
        tv.scrollTo(idx, qt.QAbstractItemView.PositionAtCenter)
    
    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()
        
        if hasattr(self, 'clippingSpheresNode') and hasattr(self, 'tagPointAddedEvent'):
            self.clippingSpheresNode.RemoveObserver(self.tagPointAddedEvent)
            del self.tagPointAddedEvent
        if hasattr(self, 'clippingSpheresNode') and hasattr(self, 'tagPointRemovedEvent'):
            self.clippingSpheresNode.RemoveObserver(self.tagPointRemovedEvent)
            del self.tagPointRemovedEvent

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
            # self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanRender)

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

        # # Select default input nodes if nothing is selected yet to save a few clicks for the user
        # if not self._parameterNode.inputVolume:
        #     firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
        #     if firstVolumeNode:
        #         self._parameterNode.inputVolume = firstVolumeNode
        
        # intensityVolume: load first
        if not self._parameterNode.intensityVolume:
           firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
           if firstVolumeNode:
               self._parameterNode.intensityVolume = firstVolumeNode
               
        if not self._parameterNode.segmentation:
           firstSegmentationNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLSegmentationNode")
           if firstSegmentationNode:
               self._parameterNode.segmentation = firstSegmentationNode
               
        if not self._parameterNode.view:
           firstViewNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLViewNode")
           if firstViewNode:
               self._parameterNode.view = firstViewNode


    def setParameterNode(self, inputParameterNode: Optional[AnatomyCarveParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            # self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanRender)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            # self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanRender)
            # self._checkCanApply()
            self._checkCanRender()

    # def _checkCanApply(self, caller=None, event=None) -> None:
    #     if self._parameterNode and self._parameterNode.inputVolume and self._parameterNode.thresholdedVolume:
    #         self.ui.applyButton.toolTip = _("Compute output volume")
    #         self.ui.applyButton.enabled = True
    #     else:
    #         self.ui.applyButton.toolTip = _("Select input and output volume nodes")
    #         self.ui.applyButton.enabled = False

    # def onApplyButton(self) -> None:
    #     """Run processing when user clicks "Apply" button."""
    #     with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
    #         # Compute output
    #         self.logic.process(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(),
    #                            self.ui.imageThresholdSliderWidget.value, self.ui.invertOutputCheckBox.checked)

    #         # Compute inverted output (if needed)
    #         if self.ui.invertedOutputSelector.currentNode():
    #             # If additional output volume is selected then result with inverted threshold is written there
    #             self.logic.process(self.ui.inputSelector.currentNode(), self.ui.invertedOutputSelector.currentNode(),
    #                                self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked, showResult=False)
                
    def _checkCanRender(self, caller=None, event=None) -> None:
        if self._parameterNode and self._parameterNode.intensityVolume and self._parameterNode.segmentation and self._parameterNode.view:
            if not hasattr(self.logic, 'context'):
                self.ui.renderButton.toolTip = _("Start AnatomyCarve rendering")
                self.ui.renderButton.enabled = True
            else:            
                self.ui.renderButton.toolTip = _("Rendering already started")
                self.ui.renderButton.enabled = False
        else:
            self.ui.renderButton.toolTip = _("Select intesnsity volume, segmentation and view nodes")
            self.ui.renderButton.enabled = False

    def onRenderButton(self) -> None:
        """Run processing when user clicks "Render" button."""
        err = glGetError()

        with slicer.util.tryWithErrorDisplay(_("Failed to start rendering."), waitCursor=True):            
            self.setupClippingSphereMarkups()
            self.logic.startRender(self.clippingSpheresNode)
            self._checkCanRender()
            


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
        # intensityVolume = SampleData.downloadSample("CTA abdomen (Panoramix)")        
        segmentation = SampleData.downloadSample("CTA abdomen (Panoramix) segmentation")
        # self.delayDisplay("Loaded test data set")

        # inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        # self.assertEqual(inputScalarRange[0], 0)
        # self.assertEqual(inputScalarRange[1], 695)

        # outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        # threshold = 100

        # Test the module logic

        logic = AnatomyCarveLogic()

        # # Test algorithm with non-inverted threshold
        # logic.process(inputVolume, outputVolume, threshold, True)
        # outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        # self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        # self.assertEqual(outputScalarRange[1], threshold)

        # # Test algorithm with inverted threshold
        # logic.process(inputVolume, outputVolume, threshold, False)
        # outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        # self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        # self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")
