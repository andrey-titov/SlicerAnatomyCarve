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
#include <vtkRendererCollection.h>

#include <qSlicerApplication.h>
#include <qMRMLLayoutManager.h>
#include <qMRMLThreeDWidget.h>
#include <qMRMLThreeDView.h>

#include <vtkMRMLScene.h>
#include <vtkMRMLVolumeNode.h>
#include <vtkMRMLVolumeRenderingDisplayNode.h>
#include <vtkRendererCollection.h>
#include <vtkRenderWindow.h>
#include <vtkRenderer.h>
#include <vtkVolumeCollection.h>
#include <vtkVolume.h>
#include <vtkVolumeMapper.h>
#include <vtkOpenGLGPUVolumeRayCastMapper.h>
#include <vtkOpenGLTexture.h>
#include <vtkImageData.h>
#include <vtkVolumeInputHelper.h>
#include <vtkVolumeTexture.h>
#include <vtkTextureObject.h>


//----------------------------------------------------------------------------
vtkStandardNewMacro(vtkSlicerVolumeTextureIDHelperLogic);

int vtkSlicerVolumeTextureIDHelperLogic::GetTextureIdForMapper(vtkOpenGLGPUVolumeRayCastMapper* mapper, int portIndex)
{
    auto it = mapper->AssembledInputs.find(portIndex);
    if (it == mapper->AssembledInputs.end())
    {
        std::cerr << "portIndex not found." << std::endl;
        return -1;
    }
    vtkVolumeInputHelper& helper = it->second;
    vtkVolumeTexture* volTex = helper.Texture;
    auto* block = volTex->GetCurrentBlock();
    if (!block)
        block = volTex->GetNextBlock();
    vtkTextureObject* texObj = block->TextureObject;
    return texObj->GetHandle();
}

int vtkSlicerVolumeTextureIDHelperLogic::GetTextureIdForVolume(vtkMRMLVolumeNode* volumeNode, int threeDViewIndex)
{
    return GetTextureIdForVolume(volumeNode, threeDViewIndex, 0);
}

int vtkSlicerVolumeTextureIDHelperLogic::GetTextureIdForVolume(vtkMRMLVolumeNode* volumeNode, int threeDViewIndex, int portIndex)
{
    if (!volumeNode || !volumeNode->GetScene())
    {
        std::cerr << "volumeNode is empty." << std::endl;
        return -1;
    }

    //vtkMRMLScene* scene = volumeNode->GetScene();

    //// Get all view nodes
    //std::vector<vtkMRMLNode*> viewNodes;
    //scene->GetNodesByClass("vtkMRMLViewNode", viewNodes);

    //if (viewIndex < 0 || viewIndex >= static_cast<int>(viewNodes.size()))
    //    return 0;

    //vtkMRMLViewNode* viewNode = vtkMRMLViewNode::SafeDownCast(viewNodes[viewIndex]);
    //if (!viewNode)
    //    return 0;

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

    QList<qMRMLThreeDView*> viewList;

    // Get the layout manager from the Slicer application
    qMRMLLayoutManager* layoutManager = qSlicerApplication::application()->layoutManager();
    if (!layoutManager)
    {
        std::cerr << "Layout manager is not available." << std::endl;
        return -1;
    }

    int viewCount3d = layoutManager->threeDViewCount();
    if (threeDViewIndex < 0)
    {
        std::cerr << "viewIndex provided is negative." << std::endl;
        return -1;
    }
    else if (threeDViewIndex >= viewCount3d)
    {
        std::cerr << "viewIndex is higher than the number of 3D views." << std::endl;
        return -1;
    }

    qMRMLThreeDWidget* widget = layoutManager->threeDWidget(threeDViewIndex);
    if (!widget)
    {
        std::cerr << "  Failed to get threeDWidget." << std::endl;
        return -1;
    }

    qMRMLThreeDView* view = widget->threeDView();
    if (!view)
    {
        std::cerr << "  Failed to get threeDView." << std::endl;
        return -1;
    }
    
    vtkRenderWindow* renderWindow = view->renderWindow();
    vtkRendererCollection* renderers = renderWindow->GetRenderers();
    vtkRenderer* renderer = renderers->GetFirstRenderer();
    if (!renderer)
    {
        std::cerr << "  No renderer found." << std::endl;
        return -1;
    }


    ////// Good so far

    vtkVolumeCollection* volumes = renderer->GetVolumes();
    volumes->InitTraversal();

    for (int i = 0; i < volumes->GetNumberOfItems(); ++i)
    {
        vtkVolume* actor = volumes->GetNextVolume();
        if (!actor || actor->GetMapper() == nullptr)
            continue;

        vtkAbstractVolumeMapper* abstractMapper = actor->GetMapper();
        vtkVolumeMapper* mapper = vtkVolumeMapper::SafeDownCast(abstractMapper);
        if (!mapper)
            continue;


        if (vtkOpenGLGPUVolumeRayCastMapper* glMapper =
            vtkOpenGLGPUVolumeRayCastMapper::SafeDownCast(mapper))
        {
            vtkDataSet* data = glMapper->GetInput();
            vtkImageData* input = vtkImageData::SafeDownCast(data);
            if (!input || volumeNode->GetImageData() != input)
                continue;

            // Ensure OpenGL context is current
            renderWindow->MakeCurrent();

            //// Access internal texture object
            //vtkTextureObject* textureManager = glMapper->GetColorTexture();
            //if (!textureManager)
            //{
            //    std::cerr << "No volume texture found." << std::endl;
            //    continue;
            //}

            return GetTextureIdForMapper(glMapper, portIndex);

            /*textureManager->

            vtkOpenGLTexture* texture = textureManager->GetTextureObject();
            if (texture)
            {
                GLuint texID = texture->GetHandle();
                std::cout << "Found texture ID: " << texID << std::endl;
                return texID;
            }*/
        }

        return -1;
    }

    std::cerr << "No matching GPU volume mapper found for the specified volume node and 3D view." << std::endl;
    return -1;
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
