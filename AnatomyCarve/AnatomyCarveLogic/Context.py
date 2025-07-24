import logging
import os
import slicer
import numpy as np
from AnatomyCarveLogic.Texture import *
from AnatomyCarveLogic.Mask import *

from OpenGL.GL import *

import vtk
from vtk.util import numpy_support

from typing import Tuple

from slicer import vtkMRMLScalarVolumeNode, vtkMRMLSegmentationNode, vtkMRMLViewNode, vtkMRMLMarkupsFiducialNode, vtkMRMLVectorVolumeNode
import vtkSegmentationCorePython as vtkSegmentationCore


class Context:
    COLOR_NUM_COMPONENTS = 4

    def __init__(self, intensityVolume: vtkMRMLScalarVolumeNode, 
                 segmentation: vtkMRMLSegmentationNode, 
                 view: vtkMRMLViewNode) -> None:
        self.intensityVolume = intensityVolume
        self.segmentation = segmentation
        self.view = view
        self.labelToColorMapTex2d = self.createLabelToColorMap()        
        self.outputVolume, self.outputVolumeTex3d = self.createVectorVolume()
        self.labelVolumeTex3d = self.createLabelVolume()
        self.labelVolumeDilatedTex3d = Texture.fromArray(np.zeros(self.labelVolumeTex3d.dims, dtype=np.uint16), GL_R16UI, GL_RED_INTEGER, GL_UNSIGNED_SHORT, True)
        self.intensityVolumeTex3d = Texture.fromVolumeNode(intensityVolume, GL_R32F, GL_RED, GL_FLOAT, 1.0)
        self.mask = Mask(segmentation, 0)
        self.labelToColorVolumeTex3d = Texture.fromArray(np.zeros(self.outputVolumeTex3d.dims + (self.COLOR_NUM_COMPONENTS,), dtype=np.uint8), GL_RGBA8, GL_RGBA, GL_UNSIGNED_BYTE, False)

    def createLabelToColorMap(self) -> Texture:
        #segNode = self.getParameterNode().segmentation           # or your node’s exact name/ID
        segmentation = self.segmentation.GetSegmentation()
        displayNode = self.segmentation.GetDisplayNode()

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

        colorMap = np.zeros((maxLabel + 1, 1, self.COLOR_NUM_COMPONENTS))

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

    def createVectorVolume(self) -> Tuple[vtkMRMLVectorVolumeNode, Texture]:
        #intensityVolume = self.getParameterNode().intensityVolume
        
        dims = self.intensityVolume.GetImageData().GetDimensions() 
        
        dims = dims[::-1]
        
        #print(dims)
        
        arrayR = np.zeros(dims, dtype=np.float32)
        arrayG = np.ones(dims, dtype=np.float32)
        arrayB = np.ones(dims, dtype=np.float32)        
        arrayA = slicer.util.arrayFromVolume(self.intensityVolume).astype(np.float32) #np.ones(dims, dtype=np.uint8)

        arrayRGBA = np.stack((arrayR, arrayG, arrayB, arrayA), axis=-1)
        
        minAlpha, maxAlpha = int(arrayA.min()), int(arrayA.max())
        #print(f"Alpha range (NumPy): min={minAlpha}, max={maxAlpha}")
        
        #print(arrayRGBA.shape)
        
        # Create new volume node
        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLVectorVolumeNode", "AnatomyCarve Output")
        slicer.util.updateVolumeFromArray(outputVolume, arrayRGBA)

        # Copy geometry (origin, spacing, matrix)
        outputVolume.SetOrigin(self.intensityVolume.GetOrigin())
        outputVolume.SetSpacing(self.intensityVolume.GetSpacing())
        matrix = vtk.vtkMatrix4x4()
        self.intensityVolume.GetIJKToRASMatrix(matrix)
        outputVolume.SetIJKToRASMatrix(matrix)

        # Show in slice view
        slicer.util.setSliceViewerLayers(background=outputVolume)

        # Optional: enable volume rendering
        volRenLogic = slicer.modules.volumerendering.logic()
        displayNode = volRenLogic.CreateDefaultVolumeRenderingNodes(outputVolume)
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
        
        textureId = slicer.modules.volumetextureidhelper.logic().GetTextureIdForVolume(outputVolume, viewIndex)
        self.visibleTextureId = textureId
        #self.rgbaVolume = rgbaVolume

        #print(textureId)
        return outputVolume, Texture.fromOpenGLTexture(textureId, self.intensityVolume.GetImageData().GetDimensions(), GL_RGBA32F, GL_RGB, GL_FLOAT)
    
    def createLabelVolume(self) -> Texture:
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
        
        
        
        #segNode = self.segmentation

        # 1. Allocate the output
        mergedLabelmap = vtkSegmentationCore.vtkOrientedImageData()

        # 2. Generate it.  Use EXTENT_REFERENCE_GEOMETRY or another extent mode.
        #    EXTENT_REFERENCE_GEOMETRY will use the segmentation’s saved reference image geometry.
        success = self.segmentation.GenerateMergedLabelmapForAllSegments(mergedLabelmap, slicer.vtkSegmentation.EXTENT_REFERENCE_GEOMETRY)
        
        if not success:
            raise RuntimeError("Failed to generate merged labelmap")

        # 3. Convert to NumPy
       
        vtkScalars = mergedLabelmap.GetPointData().GetScalars()
        arr = numpy_support.vtk_to_numpy(vtkScalars)
        dims = mergedLabelmap.GetDimensions()
        arr = arr.reshape(dims[0], dims[1], dims[2])
        # print("Multi-label shape:", arr.shape)
        
        return Texture.fromArray(arr.astype(np.uint16), GL_R16UI, GL_RED_INTEGER, GL_UNSIGNED_SHORT, True)
    

    def getViewIndex(self) -> int:
        # assume viewNode is your vtkMRMLViewNode
        layoutManager = slicer.app.layoutManager()
        nViews = layoutManager.threeDViewCount
        viewNode = self.view
        
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