import logging
import os
import slicer
import numpy as np

from OpenGL.GL import *

from slicer import vtkMRMLScalarVolumeNode, vtkMRMLSegmentationNode, vtkMRMLViewNode, vtkMRMLMarkupsFiducialNode

class CarvingConfiguration:
    def __init__(self, intensityVolume: vtkMRMLScalarVolumeNode, 
                 segmentation: vtkMRMLSegmentationNode, 
                 view: vtkMRMLViewNode) -> None:
        self.intensityVolume = intensityVolume
        self.segmentation = segmentation
        self.view = view