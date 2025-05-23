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

// VolumeTextureIDHelper Logic includes
#include "vtkSlicerVolumeTextureIDHelperLogic.h"

// MRML includes
#include <vtkMRMLScene.h>

// VTK includes
#include <vtkIntArray.h>
#include <vtkNew.h>
#include <vtkObjectFactory.h>

// STD includes
#include <cassert>

// Specific

#include <vtkMRMLVolumeNode.h>
#include <vtkMRMLViewNode.h>
#include <qSlicerApplication.h>
#include <qSlicerLayoutManager.h>
#include <qMRMLThreeDWidget.h>
#include <qMRMLThreeDView.h>

#include <vtkRenderer.h>
#include <vtkRenderWindow.h>
#include <vtkOpenGLRenderer.h>
#include <vtkVolume.h>
#include <vtkOpenGLGPUVolumeRayCastMapper.h>
#include <vtkVolumeProperty.h>
#include <vtkMRMLVolumeRenderingDisplayNode.h>
#include <vtkMRMLVolumeRenderingDisplayableManager.h>
#include <vtkSmartPointer.h>


//----------------------------------------------------------------------------
vtkStandardNewMacro(vtkSlicerVolumeTextureIDHelperLogic);

int vtkSlicerVolumeTextureIDHelperLogic::GetTextureIdForVolume(vtkMRMLVolumeNode* volumeNode, int viewIndex)
{
    if (!volumeNode || !volumeNode->GetScene())
        return 0;

    vtkMRMLScene* scene = volumeNode->GetScene();

    // Get all view nodes
    std::vector<vtkMRMLNode*> viewNodes;
    scene->GetNodesByClass("vtkMRMLViewNode", viewNodes);

    if (viewIndex < 0 || viewIndex >= static_cast<int>(viewNodes.size()))
        return 0;

    vtkMRMLViewNode* viewNode = vtkMRMLViewNode::SafeDownCast(viewNodes[viewIndex]);
    if (!viewNode)
        return 0;

    //// Get display node
    //vtkMRMLVolumeRenderingDisplayNode* displayNode = volumeNode->GetVolume GetVolumeRenderingDisplayNode();
    //if (!displayNode)
    //    return 0;

    //// Ensure the display node is active for this view
    //if (!displayNode->IsViewNodeIDPresent(viewNode->GetID()))
    //    return 0;

    //// Get vtkVolume and mapper (this part depends on internal display logic, can vary!)
    //vtkVolume* volumeActor = displayNode->GetRenderedVolume(viewNode->GetID());
    //if (!volumeActor)
    //    return 0;

    //vtkVolumeMapper* mapper = volumeActor->GetMapper();
    //auto* glMapper = vtkOpenGLVolumeTextureMapper3D::SafeDownCast(mapper);
    //if (!glMapper)
    //    return 0;

    //// Make sure OpenGL context is current (important!)
    //vtkRenderWindow* rw = displayNode->GetRenderer(viewNode->GetID())->GetRenderWindow();
    //if (rw)
    //    rw->MakeCurrent();

    //// Access OpenGL 3D texture
    //GLuint texId = glMapper->GetTextureId();
    //return texId;

    return (int) & volumeNode;
}

//----------------------------------------------------------------------------
vtkSlicerVolumeTextureIDHelperLogic::vtkSlicerVolumeTextureIDHelperLogic()
{
}

//----------------------------------------------------------------------------
vtkSlicerVolumeTextureIDHelperLogic::~vtkSlicerVolumeTextureIDHelperLogic()
{
}

//----------------------------------------------------------------------------
void vtkSlicerVolumeTextureIDHelperLogic::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
}

//---------------------------------------------------------------------------
void vtkSlicerVolumeTextureIDHelperLogic::SetMRMLSceneInternal(vtkMRMLScene * newScene)
{
  vtkNew<vtkIntArray> events;
  events->InsertNextValue(vtkMRMLScene::NodeAddedEvent);
  events->InsertNextValue(vtkMRMLScene::NodeRemovedEvent);
  events->InsertNextValue(vtkMRMLScene::EndBatchProcessEvent);
  this->SetAndObserveMRMLSceneEventsInternal(newScene, events.GetPointer());
}

//-----------------------------------------------------------------------------
void vtkSlicerVolumeTextureIDHelperLogic::RegisterNodes()
{
  assert(this->GetMRMLScene() != 0);
}

//---------------------------------------------------------------------------
void vtkSlicerVolumeTextureIDHelperLogic::UpdateFromMRMLScene()
{
  assert(this->GetMRMLScene() != 0);
}

//---------------------------------------------------------------------------
void vtkSlicerVolumeTextureIDHelperLogic
::OnMRMLSceneNodeAdded(vtkMRMLNode* vtkNotUsed(node))
{
}

//---------------------------------------------------------------------------
void vtkSlicerVolumeTextureIDHelperLogic
::OnMRMLSceneNodeRemoved(vtkMRMLNode* vtkNotUsed(node))
{
}
