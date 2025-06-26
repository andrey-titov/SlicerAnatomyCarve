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

from slicer import vtkMRMLScalarVolumeNode, vtkMRMLSegmentationNode, vtkMRMLViewNode

from OpenGL.GL import *

import numpy as np
from AnatomyCarveLogic.Texture import *
import vtkSegmentationCorePython as vtkSegmentationCore
from vtk.util import numpy_support
from AnatomyCarveLogic.ComputeShader import *


class AnatomyCarveLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return AnatomyCarveParameterNode(super().getParameterNode())

    def process(self,
                inputVolume: vtkMRMLScalarVolumeNode,
                outputVolume: vtkMRMLScalarVolumeNode,
                imageThreshold: float,
                invert: bool = False,
                showResult: bool = True) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time

        startTime = time.time()
        logging.info("Processing started")

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            "InputVolume": inputVolume.GetID(),
            "OutputVolume": outputVolume.GetID(),
            "ThresholdValue": imageThreshold,
            "ThresholdType": "Above" if invert else "Below",
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")

    def startRender(self, sphereRadius) -> None:
        self.node: AnatomyCarveParameterNode = self.getParameterNode()        
        self.labelToColor2D = self.getSegmentLabelToColorMap()
        self.volumeColor = self.createVectorVolume()
        self.labelMap = self.createLabelTexture()
        self.addCarvingSphere(sphereRadius)
        
        self.applyFillColorComputeShader()
        self.applyCarveVoxelsComputeShader()

    def getViewIndex(self) -> int:
        # assume viewNode is your vtkMRMLViewNode
        layoutManager = slicer.app.layoutManager()
        nViews = layoutManager.threeDViewCount
        viewNode = self.getParameterNode().view
        
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

    def getSegmentLabelToColorMap(self) -> Texture:
        segNode = self.getParameterNode().segmentation           # or your node’s exact name/ID
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

    
        
    def createVectorVolume(self) -> Texture:
        originalVolume = self.getParameterNode().intensityVolume
        
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
        
        
        
        segNode = self.getParameterNode().segmentation

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
        # print("Multi-label shape:", arr.shape)
        
        return Texture.fromArray(arr.astype(np.int32), GL_R32I, GL_RED_INTEGER, GL_INT, True)
    
    def addCarvingSphere(self, sphereRadius):
        # Create a new fiducial list
        carvingSphere = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Carving Sphere")

        # Add a fiducial at (x, y, z)
        carvingSphere.AddControlPoint([10.0, 20.0, 30.0]) # Coordinates in RAS

        self.sphereRadius = sphereRadius

        # print(f"Sphere radius: {self.ui.sphereRadius.value}")

        # # Optionally change display settings
        # displayNode = fiducialsNode.GetDisplayNode()
        # displayNode.SetTextScale(1.5)
        self.carvingSphere = carvingSphere

    def applyFillColorComputeShader(self):
        self.shaderFillColorVolume = ComputeShader("FillColorVolume.comp")
        shader = self.shaderFillColorVolume

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

    def applyCarveVoxelsComputeShader(self):
        self.shaderCarveVoxels = ComputeShader("CarveVoxels.comp")

        renderWindow = slicer.app.layoutManager().threeDWidget(self.getViewIndex()).threeDView().renderWindow()
        self.intensityTexture = Texture.fromVolumeNode(self.getParameterNode().intensityVolume, GL_R32F, GL_RED, GL_FLOAT)
        observerTag = renderWindow.AddObserver(vtk.vtkCommand.StartEvent, self.applyCarveVoxelsComputeShaderTick)

    def applyCarveVoxelsComputeShaderTick(self, caller, event):
        shader = self.shaderCarveVoxels

        modelMatrix = vtk.vtkMatrix4x4()
        self.rgbaVolume.GetIJKToRASMatrix(modelMatrix)

        gl_mat = np.zeros(16, dtype=np.float32)

        for col in range(4):
            for row in range(4):
                gl_mat[col * 4 + row] = modelMatrix.GetElement(row, col)

        spherePos = [0.0,0.0,0.0]
        self.carvingSphere.GetNthControlPointPosition(0, spherePos)
        self.createClipMask()

        # print(self.clipMask.shape[0])

        glUseProgram(shader.program)
        glUniform4f(glGetUniformLocation(shader.program, "sphereDetails"), spherePos[0], spherePos[1], spherePos[2], self.sphereRadius)
        glUniform1iv(glGetUniformLocation(shader.program, "clipMask"), self.clipMask.shape[0], self.clipMask)
        glUniformMatrix4fv(glGetUniformLocation(shader.program, "modelMatrix"), 1, GL_FALSE, gl_mat)
        glBindImageTexture(0, self.volumeColor.textureId, 0, GL_TRUE, 0, GL_READ_WRITE, self.volumeColor.internalformat)
        glBindImageTexture(1, self.labelMap.textureId, 0, GL_TRUE, 0, GL_READ_ONLY, self.labelMap.internalformat)
        glBindImageTexture(2, self.intensityTexture.textureId, 0, GL_TRUE, 0, GL_READ_ONLY, GL_R32F)

        shader.dispatch(self.volumeColor.dims)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

    def createClipMask(self):
        # Get the currently selected segmentation node
        segmentationNode = self.getParameterNode().segmentation  # Replace with your actual node name if needed
        
        segmentation = segmentationNode.GetSegmentation()
        displayNode = segmentationNode.GetDisplayNode()
        segmentIDs = segmentation.GetSegmentIDs()  

        # segmentInfoArray = []

        maxLabel = max(
            segmentation.GetSegment(segID).GetLabelValue() # vtkSegment::GetLabelValue 
            for segID in segmentIDs
        )

        self.clipMask = np.zeros((maxLabel + 1))

        for i in range(segmentation.GetNumberOfSegments()):
            segmentID = segmentation.GetNthSegmentID(i)
            # segment = segmentation.GetSegment(segmentID)
            isVisible = displayNode.GetSegmentVisibility(segmentID)
            labelValue = i + 1
            self.clipMask[labelValue] = 1 if bool(isVisible) else 0

        self.clipMask = self.clipMask.astype(np.int32)

        # print(self.clipMask)

        # # Example output
        # for entry in segmentInfoArray:
        #     print(entry)

#
# AnatomyCarveParameterNode
#


@parameterNodeWrapper
class AnatomyCarveParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    intensityVolume: vtkMRMLScalarVolumeNode
    segmentation: vtkMRMLSegmentationNode
    view: vtkMRMLViewNode
    inputVolume: vtkMRMLScalarVolumeNode
    imageThreshold: Annotated[float, WithinRange(-100, 500)] = 100
    invertThreshold: bool = False
    thresholdedVolume: vtkMRMLScalarVolumeNode
    invertedVolume: vtkMRMLScalarVolumeNode
