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
    @classmethod
    def fromOpenGLTexture(cls, textureId: int, dims: tuple[int], internalformat: int, format: int, type: int):
        t = cls()
        t.textureId = textureId
        t.dims = dims
        t.internalformat = internalformat
        t.format = format
        t.type = type
        return t

    # Initialize from existing volume node
    @classmethod
    def fromVolumeNode(cls, scalarVolumeNode: vtkMRMLScalarVolumeNode):
        t = cls()
        data = slicer.util.arrayFromVolume(scalarVolumeNode).astype(np.float32)
        t.uploadData(data, GL_R32F, GL_R, GL_FLOAT)
        return t

    # Initialize from new data
    @classmethod
    def fromArray(cls, data: np.ndarray, internalformat: int, format: int, type: int):
        t = cls()
        t.uploadData(data, internalformat, format, type)
        return t

    def uploadData(self, data: np.ndarray, internalformat: int, format: int, type: int):
        
        self.textureId = glGenTextures(1)
        
        self.internalformat = internalformat
        self.format = format
        self.type = type

        if len(data.shape) == 2:
            self.dims = data.shape
            glBindTexture(GL_TEXTURE_2D, self.textureId)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexStorage2D(GL_TEXTURE_2D, 1, self.internalformat, *self.dims)
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, *self.dims, self.format, self.type, data.ravel())
        elif len(data.shape) == 3:
            self.dims = data.shape[::-1]
            glBindTexture(GL_TEXTURE_3D, self.textureId)
            glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexStorage3D(GL_TEXTURE_3D, 1, self.internalformat, *self.dims)
            glTexSubImage3D(GL_TEXTURE_3D, 0, 0, 0, 0, *self.dims, self.format, self.type, data.ravel())
        else:
            logging.error(f"Arrays of dimension {len(data.shape)} are not supported")