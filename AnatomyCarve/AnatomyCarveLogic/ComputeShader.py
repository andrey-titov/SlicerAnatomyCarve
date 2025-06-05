import logging
import os
import slicer
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

from OpenGL.GL import *

from slicer import vtkMRMLScalarVolumeNode

class ComputeShader:
    SHADER_PATH = os.path.join("Resources","Shaders")
    
    def __init__(self, computeShaderPath: str):
        moduleFolder = os.path.dirname(slicer.util.modulePath("AnatomyCarve"))
        shaderPath = os.path.join(moduleFolder, self.SHADER_PATH, computeShaderPath)
        shaderCode = ""
        
        with open(shaderPath, "r") as f:
            for line in f:
                shaderCode += line
                
        print(self.createComputeShader(shaderCode))
                
    def createComputeShader(self, src):
        shader = glCreateShader(GL_COMPUTE_SHADER)
        glShaderSource(shader, src)
        glCompileShader(shader)
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            raise RuntimeError(glGetShaderInfoLog(shader).decode())
        prog = glCreateProgram()
        glAttachShader(prog, shader)
        glLinkProgram(prog)
        return prog
    
    def uploadVolumeToTexture(volumeNode : vtkMRMLScalarVolumeNode):
        array = slicer.util.arrayFromVolume(volumeNode).astype(np.float32)
        dims = array.shape[::-1]
        texID = glGenTextures(1)
        glBindTexture(GL_TEXTURE_3D, texID)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexStorage3D(GL_TEXTURE_3D, 1, GL_R32F, *dims)
        glTexSubImage3D(GL_TEXTURE_3D, 0, 0, 0, 0, *dims, GL_RED, GL_FLOAT, array.ravel())
        return texID, dims, array.shape
    
    def print(self):
        pass