import logging
import os
import slicer
from typing import Annotated, Optional

import vtk

import numpy as np

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
                
        self.program = self.createComputeShader(shaderCode)
                
    def createComputeShader(self, src):
        shader = glCreateShader(GL_COMPUTE_SHADER)
        glShaderSource(shader, src)
        glCompileShader(shader)
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            raise RuntimeError(glGetShaderInfoLog(shader).decode())
        prog = glCreateProgram()
        glAttachShader(prog, shader)
        glLinkProgram(prog)
        status = glGetProgramiv(prog, GL_LINK_STATUS)
        if not status:
            print(glGetProgramInfoLog(prog))
            raise RuntimeError("Shader program failed to link.")
        return prog
    
    def dispatch(self, threadSizeXYZ: tuple[int,int,int]):
        # Assume `program` is your linked compute shader program (GLuint)
        work_group_size = (GLint * 3)()
        glGetProgramiv(self.program, GL_COMPUTE_WORK_GROUP_SIZE, work_group_size)

        # print("Local work group size:")
        # print(f"X: {work_group_size[0]}")
        # print(f"Y: {work_group_size[1]}")
        # print(f"Z: {work_group_size[2]}")

        threadGroupsX = threadSizeXYZ[0] // work_group_size[0];
        threadGroupsY = threadSizeXYZ[1] // work_group_size[1];
        threadGroupsZ = threadSizeXYZ[2] // work_group_size[2];

        threadGroupsX += 0 if threadSizeXYZ[0] % work_group_size[0] == 0 else 1
        threadGroupsY += 0 if threadSizeXYZ[1] % work_group_size[1] == 0 else 1
        threadGroupsZ += 0 if threadSizeXYZ[2] % work_group_size[2] == 0 else 1

        glDispatchCompute(threadGroupsX, threadGroupsY, threadGroupsZ)