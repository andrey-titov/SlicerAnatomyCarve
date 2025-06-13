import logging
import os
import slicer
import numpy as np

from OpenGL.GL import *

from slicer import vtkMRMLScalarVolumeNode

# class Texture2D:
#     def __init__(self, textureId: int, dims:tuple[int], format: int) -> None:
#         self.textureId = textureId
#         self.dims = dims
#         self.format = format

#     def __init__(self, scalarVolumeNode: vtkMRMLScalarVolumeNode) -> None:
#         array = slicer.util.arrayFromVolume(scalarVolumeNode).astype(np.float32)
#         self.dims = array.shape[::-1]
#         self.textureId = glGenTextures(1)
#         self.format = GL_R32F
#         glBindTexture(GL_TEXTURE_3D, self.textureId)
#         glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
#         glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
#         glTexStorage3D(GL_TEXTURE_3D, 1, self.format, *dims)
#         glTexSubImage3D(GL_TEXTURE_3D, 0, 0, 0, 0, *dims, GL_RED, GL_FLOAT, array.ravel())

class Texture:
    # Initialize from existing OpenGL texture
    def __init__(self, textureId: int, dims: tuple[int], format: int) -> None:
        self.textureId = textureId
        self.dims = dims
        self.format = format

    # Initialize from existing volume node
    def __init__(self, scalarVolumeNode: vtkMRMLScalarVolumeNode) -> None:
        data = slicer.util.arrayFromVolume(scalarVolumeNode).astype(np.float32)
        uploadData(self, data, GL_R32F)

    # Initialize from new data
    def __init__(self, data: np.ndarray, format: int):
        uploadData(self, data, format)    

    def uploadData(self, data: np.ndarray, format: int):
        self.dims = array.shape[::-1]
        self.textureId = glGenTextures(1)
        self.format = format
        glBindTexture(GL_TEXTURE_3D, self.textureId)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexStorage3D(GL_TEXTURE_3D, 1, self.format, *dims)
        glTexSubImage3D(GL_TEXTURE_3D, 0, 0, 0, 0, *dims, GL_RED, GL_FLOAT, array.ravel())