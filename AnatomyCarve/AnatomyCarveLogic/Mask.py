import logging
import os
import slicer
import numpy as np

from OpenGL.GL import *

from AnatomyCarveLogic.Texture import *

from slicer import vtkMRMLSegmentationNode

# from qt import QOpenGLWidget
# from OpenGL.GL import glIsTexture

# from OpenGL.GL import glGetString, glGetError, GL_NO_ERROR
# from OpenGL.GL import GL_VERSION

# import traceback

class Mask:
    MAX_SPHERES = 32    
    NEW_POINT_MASK_BASED_ON_SELECTED_ROW = True

    def __init__(self, segmentation: vtkMRMLSegmentationNode, sphereCount: int) -> None:
        # # get the first 3D view’s VTK render window
        # rv = slicer.app.layoutManager().threeDWidget(0).threeDView().renderWindow()
        # # force the OpenGL context to be current here
        # rv.MakeCurrent()
        # # (re)initialize the GL context if you want
        # #rv.OpenGLInitContext()

        

        # # clear any existing error
        # # try to read the version string
        # ver = glGetString(GL_VERSION)
        # err = glGetError()

        # if err == GL_NO_ERROR and ver:
        #     print("In a valid GL context, version:", ver.decode())
        # else:
        #     print("No current GL context (or context invalid); glGetError() →", err)

        self.segmentation = segmentation
        self.texture = self.createTexture()
        self.sphereCount = sphereCount
        self.selectedSphereIndexPrevious = -1
        self.selectedSphereIndex = -1
        # self.update()

    def createTexture(self):
        segmentation = self.segmentation.GetSegmentation()
        segmentIDs = segmentation.GetSegmentIDs()  

        maxLabel = max(
            segmentation.GetSegment(segID).GetLabelValue() # vtkSegment::GetLabelValue 
            for segID in segmentIDs
        )
        return Texture.fromArray(np.ones((maxLabel + 1, self.MAX_SPHERES), dtype=np.int32), GL_R8UI, GL_RED_INTEGER, GL_UNSIGNED_BYTE, True)
    
    def addSphere(self):
        self.sphereCount += 1
        
        if self.sphereCount == 1:
            self.updateRowFromSegmentation(0)
        else:
            if self.NEW_POINT_MASK_BASED_ON_SELECTED_ROW:
                rowMask = self.texture.readRow2d(self.selectedSphereIndex)
            else:
                rowMask = self.texture.readRow2d(self.sphereCount - 2)
            self.texture.updateRow2d(self.sphereCount - 1, rowMask)
        
        self.selectedSphereIndexPrevious = self.selectedSphereIndex
        self.selectSphere(self.sphereCount - 1)
        
        
        
        # if self.sphereCount <= 1:
        #     return
        
        # previousLastIndex = self.sphereCount - 1
        # newLastIndex = self.sphereCount
        
        # for x in range(self.texture.dims[0]):
        #     pass
        #print(self.texture.readRow2d(0))
        
    def selectSphere(self, index: int):
        
        self.selectedSphereIndex = index
        
        rowMask = self.texture.readRow2d(index)
        
        segmentation = self.segmentation.GetSegmentation()
        displayNode = self.segmentation.GetDisplayNode()

        for i in range(segmentation.GetNumberOfSegments()):
            segmentID = segmentation.GetNthSegmentID(i)
            segment = segmentation.GetSegment(segmentID)
            labelValue = segment.GetLabelValue()
            visibility = rowMask[labelValue] == 1
            displayNode.SetSegmentVisibility(segmentID, visibility)
    
    def removeSphere(self):
        if self.sphereCount <= 0:
            self.selectedSphereIndex = -1
            return
        
        self.sphereCount -= 1
        
        if (self.sphereCount <= 0):
            self.selectedSphereIndex = -1
            return
        
        if (self.selectedSphereIndex >= self.sphereCount):
            if self.NEW_POINT_MASK_BASED_ON_SELECTED_ROW:
                if (self.selectedSphereIndexPrevious >= self.sphereCount):
                    self.selectSphere(self.sphereCount - 1)
                else:
                    self.selectSphere(self.selectedSphereIndexPrevious)
            else:
                self.selectSphere(self.sphereCount - 1)
            
    def updateSelectedRowFromSegmentation(self):
        self.updateRowFromSegmentation(self.selectedSphereIndex)
        
    def updateRowFromSegmentation(self, rowIndex: int):

        

        # # get the first 3D view’s VTK render window
        # rv = slicer.app.layoutManager().threeDWidget(0).threeDView().renderWindow()
        # # force the OpenGL context to be current here
        # rv.MakeCurrent()
        # # (re)initialize the GL context if you want
        # #rv.OpenGLInitContext()

        # # clear any existing error
        # err = glGetError()
        # if err == GL_INVALID_VALUE:
        #     print("Detected GL_INVALID_VALUE (1281); dumping Python stack:")
        #     traceback.print_stack()
        
        # # try to read the version string
        # ver = glGetString(GL_VERSION)
        # err = glGetError()

        # if err == GL_NO_ERROR and ver:
        #     print("In a valid GL context, version:", ver.decode())
        # else:
        #     print("No current GL context (or context invalid); glGetError() →", err)

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
            segment = segmentation.GetSegment(segmentID)
            isVisible = displayNode.GetSegmentVisibility(segmentID)
            labelValue = segment.GetLabelValue()
            rowMask[labelValue] = 1 if bool(isVisible) else 0

        # print(rowMask)
        if self.sphereCount >= 1:
            self.texture.updateRow2d(rowIndex, rowMask)