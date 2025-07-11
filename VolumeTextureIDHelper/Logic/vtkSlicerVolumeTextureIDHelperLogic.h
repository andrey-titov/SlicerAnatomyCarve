/*==============================================================================

  Program: 3D Slicer

  Portions (c) Copyright Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

==============================================================================*/

// .NAME vtkSlicerVolumeTextureIDHelperLogic - slicer logic class for volumes manipulation
// .SECTION Description
// This class manages the logic associated with reading, saving,
// and changing propertied of the volumes


#ifndef __vtkSlicerVolumeTextureIDHelperLogic_h
#define __vtkSlicerVolumeTextureIDHelperLogic_h

// Slicer includes
#include "vtkSlicerModuleLogic.h"

// MRML includes

// STD includes
#include <cstdlib>

#include "vtkSlicerVolumeTextureIDHelperModuleLogicExport.h"

// Specific
#include <vtkObject.h>
#include <vtkSmartPointer.h>
#include <vtkMRMLVolumeNode.h>
#include <vtkOpenGLGPUVolumeRayCastMapper.h>

#include <vtkSlicerVolumeRenderingLogic.h>


class VTK_SLICER_VOLUMETEXTUREIDHELPER_MODULE_LOGIC_EXPORT vtkSlicerVolumeTextureIDHelperLogic :
  public vtkSlicerModuleLogic
{
public:

  static vtkSlicerVolumeTextureIDHelperLogic *New();
  vtkTypeMacro(vtkSlicerVolumeTextureIDHelperLogic, vtkSlicerModuleLogic);
  void PrintSelf(ostream& os, vtkIndent indent) override;

  /// Gets the OpenGL texture ID used by the mapper in a specific view index
  int GetTextureIdForMapper(vtkOpenGLGPUVolumeRayCastMapper* mapper, int portIndex);
  int GetTextureIdForVolume(vtkMRMLVolumeNode* volumeNode, int threeDViewIndex);
  int GetTextureIdForVolume(vtkMRMLVolumeNode* volumeNode, int threeDViewIndex, int portIndex);

protected:
  vtkSlicerVolumeTextureIDHelperLogic();
  ~vtkSlicerVolumeTextureIDHelperLogic() override;

  void SetMRMLSceneInternal(vtkMRMLScene* newScene) override;
  /// Register MRML Node classes to Scene. Gets called automatically when the MRMLScene is attached to this logic class.
  void RegisterNodes() override;
  void UpdateFromMRMLScene() override;
  void OnMRMLSceneNodeAdded(vtkMRMLNode* node) override;
  void OnMRMLSceneNodeRemoved(vtkMRMLNode* node) override;
private:

  vtkSlicerVolumeTextureIDHelperLogic(const vtkSlicerVolumeTextureIDHelperLogic&); // Not implemented
  void operator=(const vtkSlicerVolumeTextureIDHelperLogic&); // Not implemented  
};

#endif
