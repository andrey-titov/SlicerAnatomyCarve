import logging
import os
import slicer
import numpy as np

from OpenGL.GL import *

from AnatomyCarveLogic.Texture import *

from slicer import vtkMRMLSegmentationNode

class Mask:
    MAX_SPHERES = 32

    def __init__(self, segmentation: vtkMRMLSegmentationNode, sphereCount: int) -> None:
        self.segmentation = segmentation
        self.texture = self.createTexture()
        self.sphereCount = sphereCount
        self.update()

    def createTexture(self):
        segmentation = self.segmentation.GetSegmentation()
        segmentIDs = segmentation.GetSegmentIDs()  

        maxLabel = max(
            segmentation.GetSegment(segID).GetLabelValue() # vtkSegment::GetLabelValue 
            for segID in segmentIDs
        )
        return Texture.fromArray(np.ones((maxLabel + 1, self.MAX_SPHERES), dtype=np.int32), GL_R32I, GL_RED_INTEGER, GL_INT, True)
    
    def addSphere(self):
        self.sphereCount += 1
        self.update()
        
        # if self.sphereCount <= 1:
        #     return
        
        # previousLastIndex = self.sphereCount - 1
        # newLastIndex = self.sphereCount
        
        # for x in range(self.texture.dims[0]):
        #     pass
        #print(self.texture.readRow2d(0))
        
    def removeSphere(self):
        if self.sphereCount <= 0:
            return
        
        self.sphereCount -= 1
        
        if (self.sphereCount <= 0):
            return
        
        
            

    def update(self):
        # Get the currently selected segmentation node
        #segmentation = self.getParameterNode().segmentation  # Replace with your actual node name if needed
        
        segmentation = self.segmentation.GetSegmentation()
        displayNode = self.segmentation.GetDisplayNode()
        #segmentIDs = segmentation.GetSegmentIDs()  

        # segmentInfoArray = []
        # self.clipMask = np.zeros((maxLabel + 1))

        rowMask = np.zeros((self.texture.dims[0]), dtype=np.int32)

        for i in range(segmentation.GetNumberOfSegments()):
            segmentID = segmentation.GetNthSegmentID(i)
            # segment = segmentation.GetSegment(segmentID)
            isVisible = displayNode.GetSegmentVisibility(segmentID)
            labelValue = i + 1
            rowMask[labelValue] = 1 if bool(isVisible) else 0

        # print(rowMask)
        if self.sphereCount >= 1:
            self.texture.updateRow2d(self.sphereCount - 1, rowMask)