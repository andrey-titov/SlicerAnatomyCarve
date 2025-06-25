import logging
import os
import time
from typing import Annotated, Optional

import vtk

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode

try:
    from OpenGL.GL import *
except ImportError:
    slicer.util.pip_install('PyOpenGL')


from AnatomyCarveLogic import *
import numpy as np
from AnatomyCarveLogic.Texture import *
import vtkSegmentationCorePython as vtkSegmentationCore
from vtk.util import numpy_support



#
# AnatomyCarve
#


class AnatomyCarve(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("AnatomyCarve")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#AnatomyCarve">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
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
        sampleName="AnatomyCarve1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "AnatomyCarve1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="AnatomyCarve1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="AnatomyCarve1",
    )

    # AnatomyCarve2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="AnatomyCarve",
        sampleName="AnatomyCarve2",
        thumbnailFileName=os.path.join(iconsPath, "AnatomyCarve2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="AnatomyCarve2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="AnatomyCarve2",
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

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

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
        #self.logic.startRender() TODO: put into logic class
        self.startRender()

    def startRender(self) -> None:
        self.node: AnatomyCarveParameterNode = self.logic.getParameterNode()        
        self.labelToColor2D = self.getSegmentLabelToColorMap()
        self.volumeColor = self.createVectorVolume()
        self.labelMap = self.createLabelTexture()
        #self.applyNoiseComputeShader()
        self.addCarvingSphere()
        self.applyFillColorComputeShader()
        # self.applyDilationComputeShader()
        self.applyCarveVoxelsComputeShader()

    def getSegmentLabelToColorMap(self) -> Texture:
        segNode = self.logic.getParameterNode().segmentation           # or your node’s exact name/ID
        segmentation = segNode.GetSegmentation()
        displayNode = segNode.GetDisplayNode()

        # 2. Get the list of segment IDs
        segmentIDs = segmentation.GetSegmentIDs()                 # vtkSegmentation::GetSegmentIDs :contentReference[oaicite:0]{index=0}

        # 3. Build a mapping from label value → RGB color
        labelColorMapping = {}
        for segID in segmentIDs:
            seg = segmentation.GetSegment(segID)
            labelValue = seg.GetLabelValue()                      # vtkSegment::GetLabelValue :contentReference[oaicite:1]{index=1}

            # get the actual display color (including any overrides)
            r, g, b = displayNode.GetSegmentColor(segID)          # vtkMRMLSegmentationDisplayNode::GetSegmentColor :contentReference[oaicite:2]{index=2}

            labelColorMapping[labelValue] = (r, g, b)

        # 4. Compute the maximum label value
        maxLabel = max(
            segmentation.GetSegment(segID).GetLabelValue() # vtkSegment::GetLabelValue 
            for segID in segmentIDs
        )

        NUM_COMPONENTS = 4

        colorMap = np.zeros((maxLabel + 1, 1, NUM_COMPONENTS))

        for label in labelColorMapping:
            colorMap[label, 0, 0] = labelColorMapping[label][0]
            colorMap[label, 0, 1] = labelColorMapping[label][1]
            colorMap[label, 0, 2] = labelColorMapping[label][2]
            colorMap[label, 0, 3] = 1.0

        colorMap[0, 0, 3] = 0.0

        #print(colorMap.shape)
        
        # ## TODO: Remove
        # for i in range(colorMap.shape[0]):
        #     colorMap[i, 0, 0] = 255
        #     colorMap[i, 0, 1] = 255
        #     colorMap[i, 0, 2] = 0
        #     colorMap[i, 0, 3] = 255
        
        colorMap *= 255.0
        

        return Texture.fromArray(colorMap.astype(np.uint8), GL_RGBA8, GL_RGBA, GL_UNSIGNED_BYTE, False)

        ## 4. Print it out
        #print("Label → Color mapping:")
        #for label, (r, g, b) in sorted(labelColorMapping.items()):
        #print(f"  • Label {label:3d} → (R={r:.3f}, G={g:.3f}, B={b:.3f})")

    def getViewIndex(self) -> int:
        # assume viewNode is your vtkMRMLViewNode
        layoutManager = slicer.app.layoutManager()
        nViews = layoutManager.threeDViewCount
        viewNode = self.logic.getParameterNode().view
        
        viewIndex = -1
        for i in range(nViews):
            # get the i-th 3D widget
            threeDWidget = layoutManager.threeDWidget(i)
            # get its view node
            vn = threeDWidget.threeDView().mrmlViewNode()
            if vn.GetID() == viewNode.GetID():
                viewIndex = i
                break
        return viewIndex
        
    def createVectorVolume(self) -> Texture:
        originalVolume = self.logic.getParameterNode().intensityVolume
        
        dims = originalVolume.GetImageData().GetDimensions() 
        
        dims = dims[::-1]
        
        #print(dims)
        
        arrayR = np.zeros(dims, dtype=np.float32)
        arrayG = np.ones(dims, dtype=np.float32)
        arrayB = np.ones(dims, dtype=np.float32)        
        arrayA = slicer.util.arrayFromVolume(originalVolume).astype(np.float32) #np.ones(dims, dtype=np.uint8)

        arrayRGBA = np.stack((arrayR, arrayG, arrayB, arrayA), axis=-1)
        
        minAlpha, maxAlpha = int(arrayA.min()), int(arrayA.max())
        #print(f"Alpha range (NumPy): min={minAlpha}, max={maxAlpha}")
        
        #print(arrayRGBA.shape)
        
        # Create new volume node
        rgbaVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLVectorVolumeNode", "RGBA_Volume")
        slicer.util.updateVolumeFromArray(rgbaVolume, arrayRGBA)

        # Copy geometry (origin, spacing, matrix)
        rgbaVolume.SetOrigin(originalVolume.GetOrigin())
        rgbaVolume.SetSpacing(originalVolume.GetSpacing())
        matrix = vtk.vtkMatrix4x4()
        originalVolume.GetIJKToRASMatrix(matrix)
        rgbaVolume.SetIJKToRASMatrix(matrix)

        # Show in slice view
        slicer.util.setSliceViewerLayers(background=rgbaVolume)

        # Optional: enable volume rendering
        volRenLogic = slicer.modules.volumerendering.logic()
        displayNode = volRenLogic.CreateDefaultVolumeRenderingNodes(rgbaVolume)
        displayNode.SetVisibility(True)
        #displayNode.GetVolumePropertyNode().GetVolumeProperty().SetIndependentComponents(0)
        
        vpNode = displayNode.GetVolumePropertyNode()
        
        vp = displayNode.GetVolumePropertyNode().GetVolumeProperty()

        # 1. Direct RGB colors + raw alpha
        vp.SetIndependentComponents(0)

        # 2. Identity scalar-opacity TF on component 3 → α
        so = vp.GetScalarOpacity()
        so.RemoveAllPoints()
        so.AddPoint(  minAlpha, 0.0 )  # α=0 → transparent
        so.AddPoint(maxAlpha, 1.0 )  # α=255 → opaque

        # 3. Disable gradient-based opacity
        go = vp.GetGradientOpacity()
        go.RemoveAllPoints()
        go.AddPoint( minAlpha, 0.0 )
        go.AddPoint(maxAlpha, 1.0 )

        # 4. (Optional) Turn off lighting so you don’t get any shading dimming
        #vp.ShadeOff()

        # Refresh the VR display
        displayNode.GetVolumePropertyNode().Modified()
        
        
        #vp = vpNode.GetVolumeProperty()               # vtkVolumeProperty
        #vp.ShadeOff()                                 # equivalent to SetShade(0)
        #vpNode.Modified()                             # notify the MRML node of the change
        
        viewIndex = self.getViewIndex()

        # if viewIndex is not None:
        #     print(f"ViewNode {viewNode.GetName()} has index {viewIndex}")
        # else:
        #     print("ViewNode is not currently in any visible 3D view.")
        
        textureId = slicer.modules.volumetextureidhelper.logic().GetTextureIdForVolume(rgbaVolume, viewIndex)
        self.visibleTextureId = textureId
        self.rgbaVolume = rgbaVolume

        #print(textureId)
        return Texture.fromOpenGLTexture(textureId, originalVolume.GetImageData().GetDimensions(), GL_RGBA32F, GL_RGB, GL_FLOAT)
        
    def createLabelTexture(self) -> Texture:
        # # 1. Get your segmentation node (by name, or just grab the first one)
        # segNode = self.logic.getParameterNode().segmentation  # replace with your node’s actual name
        # # segNode = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLSegmentationNode')
        # segNode.SetReferenceImageGeometryParameterFromVolumeNode(self.logic.getParameterNode().intensityVolume)

        # # 2. Create a label‐map volume node to receive the export
        # labelmapNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode', 'LabelMap_AnatomyCarve')

        # # 3. Use the segmentation logic to export all segments into that label‐map
        # segLogic = slicer.modules.segmentations.logic()
        # segLogic.ExportAllSegmentsToLabelmapNode(segNode, labelmapNode)

        # # 4. Now grab the raw array from the exported labelmap volume
        # #    This is a 3D NumPy array of ints, where each voxel’s value is the segment index.
        # array = slicer.util.arrayFromVolume(labelmapNode).astype(np.int16)
        # print(array.shape, array.dtype)
        
        
        
        segNode = self.logic.getParameterNode().segmentation

        # 1. Allocate the output
        mergedLabelmap = vtkSegmentationCore.vtkOrientedImageData()

        # 2. Generate it.  Use EXTENT_REFERENCE_GEOMETRY or another extent mode.
        #    EXTENT_REFERENCE_GEOMETRY will use the segmentation’s saved reference image geometry.
        success = segNode.GenerateMergedLabelmapForAllSegments(mergedLabelmap, slicer.vtkSegmentation.EXTENT_REFERENCE_GEOMETRY)
        
        if not success:
            raise RuntimeError("Failed to generate merged labelmap")

        # 3. Convert to NumPy
       
        vtkScalars = mergedLabelmap.GetPointData().GetScalars()
        arr = numpy_support.vtk_to_numpy(vtkScalars)
        dims = mergedLabelmap.GetDimensions()
        arr = arr.reshape(dims[0], dims[1], dims[2])
        print("Multi-label shape:", arr.shape)
        
        return Texture.fromArray(arr.astype(np.int32), GL_R32I, GL_RED_INTEGER, GL_INT, True)
    
    def applyCarveVoxelsComputeShader(self):
        self.shader = ComputeShader("CarveVoxels.comp")

        renderWindow = slicer.app.layoutManager().threeDWidget(self.getViewIndex()).threeDView().renderWindow()

        observerTag = renderWindow.AddObserver(vtk.vtkCommand.StartEvent, self.applyCarveVoxelsComputeShaderTick)

    def applyNoiseComputeShader(self):
        self.shader = ComputeShader("Noise.comp")

        # Get the render window from the 3D viewer
        renderWindow = slicer.app.layoutManager().threeDWidget(self.getViewIndex()).threeDView().renderWindow()

        self.frame = 0
        self.frameCount = 0
        self.lastTime = time.time()
        
        # Add observer for before-render event
        observerTag = renderWindow.AddObserver(vtk.vtkCommand.StartEvent, self.applyNoiseComputeShaderTick)
    
    def applyCarveVoxelsComputeShaderTick(self, caller, event):
        shader = self.shader

        modelMatrix = vtk.vtkMatrix4x4()
        self.rgbaVolume.GetIJKToRASMatrix(modelMatrix)

        gl_mat = np.zeros(16, dtype=np.float32)

        for col in range(4):
            for row in range(4):
                gl_mat[col * 4 + row] = modelMatrix.GetElement(row, col)

        glUseProgram(shader.program)
        # TODO: replace these values with the proper sphere values, x,y,z and w as the radius
        glUniform4f(glGetUniformLocation(shader.program, "sphereDetails"), 0.0, 0.0, 0.0, 200.0)
        glUniformMatrix4fv(glGetUniformLocation(shader.program, "modelMatrix"), 1, GL_FALSE, gl_mat)
        glBindImageTexture(0, self.volumeColor.textureId, 0, GL_TRUE, 0, GL_WRITE_ONLY, self.volumeColor.internalformat)

        shader.dispatch(self.volumeColor.dims)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

    def applyNoiseComputeShaderTick(self, caller, event):

        shader = self.shader

        glUseProgram(shader.program)
        glBindImageTexture(0, self.volumeColor.textureId, 0, GL_TRUE, 0, GL_WRITE_ONLY, GL_RGBA32F)
        glUniform1f(glGetUniformLocation(shader.program, "scale"), 0.00025)
        glUniform1ui(glGetUniformLocation(shader.program, "frame"), self.frame)
        #print(self.volumeColor.dims)
        shader.dispatch(self.volumeColor.dims)        
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

        self.frame += 1
        self.frameCount += 1
        now = time.time()
        if now - self.lastTime >= 1.0:
            print(f"FPS: {self.frameCount}")
            frameCount = 0
            lastTime = now

    def addCarvingSphere(self):
        # Create a new fiducial list
        carvingSphere = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Carving Sphere")

        # Add a fiducial at (x, y, z)
        carvingSphere.AddControlPoint([10.0, 20.0, 30.0]) # Coordinates in RAS

        print(f"Sphere radius: {self.ui.sphereRadius.value}")

        # # Optionally change display settings
        # displayNode = fiducialsNode.GetDisplayNode()
        # displayNode.SetTextScale(1.5)

    def applyFillColorComputeShader(self):
        self.shader = ComputeShader("FillColorVolume.comp")
        shader = self.shader

        # Get the render window from the 3D viewer
        renderWindow = slicer.app.layoutManager().threeDWidget(self.getViewIndex()).threeDView().renderWindow()

        glUseProgram(shader.program)
        glBindImageTexture(0, self.labelMap.textureId, 0, GL_TRUE, 0, GL_READ_ONLY, self.labelMap.internalformat)
        glBindImageTexture(1, self.labelToColor2D.textureId, 0, GL_TRUE, 0, GL_READ_ONLY, self.labelToColor2D.internalformat)
        glBindImageTexture(2, self.volumeColor.textureId, 0, GL_TRUE, 0, GL_WRITE_ONLY, self.volumeColor.internalformat)
        glUniform1f(glGetUniformLocation(shader.program, "scale"), 0.00025)
        glUniform1i(glGetUniformLocation(shader.program, "colorMapSize"), self.labelToColor2D.dims[0])
        shader.dispatch(self.volumeColor.dims)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

    def applyDilationComputeShader(self):
        dilationShader = ComputeShader("DilateColorVolume.comp")

        renderWindow = slicer.app.layoutManager().threeDWidget(self.getViewIndex()).threeDView().renderWindow()

        originalVolume = self.logic.getParameterNode().intensityVolume
        outputGrid = Texture.fromOpenGLTexture(self.textureId, originalVolume.GetImageData().GetDimensions(), GL_RGBA32F, GL_RGB, GL_FLOAT)
        glUseProgram(dilationShader.program)
        glBindImageTexture(0, self.volumeColor.textureId, 0, GL_TRUE, 0, GL_READ_ONLY, self.volumeColor.internalformat)
        glBindImageTexture(1, outputGrid.textureId, 0, GL_TRUE, 0, GL_WRITE_ONLY, outputGrid.internalformat)
        glBindImageTexture(2, self.labelMap.textureId, 0, GL_TRUE, 0, GL_READ_ONLY, self.labelMap.internalformat)
        dilationShader.dispatch(self.volumeColor.dims)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

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
