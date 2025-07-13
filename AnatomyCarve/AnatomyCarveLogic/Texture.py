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
    def fromOpenGLTexture(cls, textureId: int, dims: tuple[int, int, int], internalformat: int, format: int, type: int):
        t = cls()
        t.textureId = textureId
        t.dims = dims
        t.internalformat = internalformat
        t.format = format
        t.type = type
        return t

    # Initialize from existing volume node
    @classmethod
    def fromVolumeNode(cls, scalarVolumeNode: vtkMRMLScalarVolumeNode, internalformat: int, format: int, type: int):
        t = cls()
        data = slicer.util.arrayFromVolume(scalarVolumeNode).astype(np.float32)
        data = data.reshape(data.shape[::-1])
        min = data.min()
        max = data.max()
        data = (data - min) / (max - min)
        # data = 
        t.uploadData(data, internalformat, format, type, True)
        return t

    # Initialize from new data
    @classmethod
    def fromArray(cls, data: np.ndarray, internalformat: int, format: int, type: int, isScalarComponent: bool):
        t = cls()
        t.uploadData(data, internalformat, format, type, isScalarComponent)
        return t

    def uploadData(self, data: np.ndarray, internalformat: int, format: int, type: int, isScalarComponent: bool):
        self.dims = data.shape if isScalarComponent else data.shape[:-1]
        # print(self.dims)
        
        self.textureId = glGenTextures(1)
        
        self.internalformat = internalformat
        self.format = format
        self.type = type

        if len(self.dims) == 2: #isScalarComponent and len(data.shape) == 2 or not isScalarComponent and len(data.shape) == 3: 
            glBindTexture(GL_TEXTURE_2D, self.textureId)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexStorage2D(GL_TEXTURE_2D, 1, self.internalformat, *self.dims)
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, *self.dims, self.format, self.type, data.ravel())
        elif len(self.dims) == 3: #isScalarComponent and len(data.shape) == 3 or not isScalarComponent and len(data.shape) == 4:
            glBindTexture(GL_TEXTURE_3D, self.textureId)
            glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexStorage3D(GL_TEXTURE_3D, 1, self.internalformat, *self.dims)
            glTexSubImage3D(GL_TEXTURE_3D, 0, 0, 0, 0, *self.dims, self.format, self.type, data.ravel())
        else:
            logging.error(f"Arrays of dimension {len(data.shape)} are not supported")

    def updateRow2d(self, rowIndex: int, newRow: np.ndarray):
        glBindTexture(GL_TEXTURE_2D, self.textureId)

        # Set unpack alignment to 1 to avoid issues with row padding
        #glPixelStorei(GL_UNPACK_ALIGNMENT, 4)

        glTexSubImage2D(
            GL_TEXTURE_2D,
            0,                     # mipmap level
            0, rowIndex,      # xoffset, yoffset
            newRow.shape[0], 1,      # width, height
            self.format,                # format (single channel)
            self.type,      # type
            newRow.ravel()               # numpy array with shape (width,)
        )