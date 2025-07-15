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

from slicer import vtkMRMLScalarVolumeNode, vtkMRMLSegmentationNode, vtkMRMLViewNode, vtkMRMLMarkupsFiducialNode

from OpenGL.GL import *

import numpy as np
from AnatomyCarveLogic.Texture import *
from AnatomyCarveLogic.Context import *
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
        self.shaderFillColorVolume = ComputeShader("FillColorVolume.comp")
        self.shaderCarveVoxels = ComputeShader("CarveVoxels.comp")

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

    def startRender(self, clippingSpheresNode: vtkMRMLMarkupsFiducialNode) -> None:
        self.node: AnatomyCarveParameterNode = self.getParameterNode()
        self.clippingSpheresNode = clippingSpheresNode

        self.context = Context(self.node.intensityVolume, self.node.segmentation, self.node.view)

        self.addInitialClippingSphere()
        
        self.applyFillColorComputeShader()
        self.applyCarveVoxelsComputeShader()


    def addLastClippingSphere(self, sphereRadius: int):
        #print(updatedPoints)
        # print(self.context.mask.texture.readRow2d(0))
        
        lastIndex = self.clippingSpheresNode.GetNumberOfControlPoints() - 1
        self.sphereRadiuses[self.clippingSpheresNode.GetNthControlPointID(lastIndex)] = sphereRadius
        self.context.mask.addSphere()

    def removeLastClippingSphere(self):
        pass
        #print(updatedPoints)
    
    def addInitialClippingSphere(self):
        # Create a new fiducial list
        #carvingSphere = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Carving Sphere")

        # 2. Grab its display node
        #dispNode = carvingSphere.GetDisplayNode()

        # Add a fiducial at (x, y, z)
        self.sphereRadiuses = dict()
        
        self.clippingSpheresNode.AddControlPoint([0.0, 0.0, 0.0]) # Coordinates in RAS
        
        # n = self.clippingSpheresNode.GetNumberOfControlPoints()
        # self.addLastClippingSphere([tuple(self.clippingSpheresNode.GetNthControlPointID(i)) for i in range(n)])

        # # 3. Disable all snapping
        # #    this sets SnapMode → SnapModeUnconstrained (no snapping to surfaces)
        # dispNode.SetSnapMode(slicer.vtkMRMLMarkupsDisplayNode.SnapModeUnconstrained)  

        # # 4. Enable occluded‐visibility
        # #    this makes the fiducials remain visible even when they are behind other geometry
        # dispNode.SetOccludedVisibility(True)   
        # #    and you can control how “solid” they appear when occluded
        # dispNode.SetOccludedOpacity(1.0)         # 1.0 = fully opaque when occluded

        #self.sphereRadius = sphereRadius

        # print(f"Sphere radius: {self.ui.sphereRadius.value}")

        # # Optionally change display settings
        # displayNode = fiducialsNode.GetDisplayNode()
        # displayNode.SetTextScale(1.5)
        # self.carvingSphere = carvingSphere

    def applyFillColorComputeShader(self):
        
        shader = self.shaderFillColorVolume

        # Get the render window from the 3D viewer
        renderWindow = slicer.app.layoutManager().threeDWidget(self.context.getViewIndex()).threeDView().renderWindow()

        glUseProgram(shader.program)
        shader.bindTexture(0, self.context.labelVolumeTex3d, GL_READ_ONLY)
        shader.bindTexture(1, self.context.labelToColorMapTex2d, GL_READ_ONLY)
        shader.bindTexture(2, self.context.labelToColorVolumeTex3d, GL_WRITE_ONLY)
        glUniform1f(glGetUniformLocation(shader.program, "scale"), 0.00025)
        glUniform1i(glGetUniformLocation(shader.program, "colorMapSize"), self.context.labelToColorMapTex2d.dims[0])
        # print(self.context.labelToColorVolumeTex3d.dims)
        shader.dispatch(self.context.labelToColorVolumeTex3d.dims)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

    def applyCarveVoxelsComputeShader(self):
        

        renderWindow = slicer.app.layoutManager().threeDWidget(self.context.getViewIndex()).threeDView().renderWindow()
        
        observerTag = renderWindow.AddObserver(vtk.vtkCommand.StartEvent, self.applyCarveVoxelsComputeShaderTick)

    def applyCarveVoxelsComputeShaderTick(self, caller, event):
        shader = self.shaderCarveVoxels

        modelMatrix = vtk.vtkMatrix4x4()
        self.context.outputVolume.GetIJKToRASMatrix(modelMatrix)

        gl_mat = np.zeros(16, dtype=np.float32)

        for col in range(4):
            for row in range(4):
                gl_mat[col * 4 + row] = modelMatrix.GetElement(row, col)

        sphereDetailsArray = []
        for i in range(self.clippingSpheresNode.GetNumberOfControlPoints()):
            spherePosRadius = [0.0,0.0,0.0]
            self.clippingSpheresNode.GetNthControlPointPosition(i, spherePosRadius)
            spherePosRadius.append(self.sphereRadiuses[self.clippingSpheresNode.GetNthControlPointID(i)])
            sphereDetailsArray.append(spherePosRadius)
        
        sphereDetails = np.array(sphereDetailsArray, dtype=np.float32)
        
        self.context.mask.update()
        
        #self.context.mask.texture.readRow2d(0)

        # print(self.clipMask.shape[0])

        glUseProgram(shader.program)
        glUniform4fv(glGetUniformLocation(shader.program, "sphereDetails"), 32, sphereDetails)
        glUniform1i(glGetUniformLocation(shader.program, "sphereCount"), self.context.mask.sphereCount)
        #glUniform1iv(glGetUniformLocation(shader.program, "clipMask"), self.clipMask.shape[0], self.clipMask)
        glUniformMatrix4fv(glGetUniformLocation(shader.program, "modelMatrix"), 1, GL_FALSE, gl_mat)
        shader.bindTexture(0, self.context.outputVolumeTex3d, GL_READ_WRITE)
        shader.bindTexture(1, self.context.labelVolumeTex3d, GL_READ_ONLY)
        shader.bindTexture(2, self.context.intensityVolumeTex3d, GL_READ_ONLY)
        shader.bindTexture(3, self.context.mask.texture, GL_READ_ONLY)
        shader.bindTexture(4, self.context.labelToColorVolumeTex3d, GL_READ_ONLY)

        shader.dispatch(self.context.labelToColorVolumeTex3d.dims)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

    # def createClipMask(self):
    #     # Get the currently selected segmentation node
    #     segmentationNode = self.getParameterNode().segmentation  # Replace with your actual node name if needed
        
    #     segmentation = segmentationNode.GetSegmentation()
    #     displayNode = segmentationNode.GetDisplayNode()
    #     segmentIDs = segmentation.GetSegmentIDs()  

    #     # segmentInfoArray = []

    #     maxLabel = max(
    #         segmentation.GetSegment(segID).GetLabelValue() # vtkSegment::GetLabelValue 
    #         for segID in segmentIDs
    #     )

    #     self.clipMask = np.zeros((maxLabel + 1))

    #     for i in range(segmentation.GetNumberOfSegments()):
    #         segmentID = segmentation.GetNthSegmentID(i)
    #         # segment = segmentation.GetSegment(segmentID)
    #         isVisible = displayNode.GetSegmentVisibility(segmentID)
    #         labelValue = i + 1
    #         self.clipMask[labelValue] = 1 if bool(isVisible) else 0

    #     self.clipMask = self.clipMask.astype(np.int32)

    #     # print(self.clipMask)

    #     # # Example output
    #     # for entry in segmentInfoArray:
    #     #     print(entry)

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
    carvingSphere: vtkMRMLMarkupsFiducialNode
