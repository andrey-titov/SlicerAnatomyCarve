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
#include <vtkSlicerVolumeTextureIDHelperLogic.h>

// VolumeTextureIDHelper includes
#include "qSlicerVolumeTextureIDHelperModule.h"
#include "qSlicerVolumeTextureIDHelperModuleWidget.h"

//-----------------------------------------------------------------------------
class qSlicerVolumeTextureIDHelperModulePrivate
{
public:
  qSlicerVolumeTextureIDHelperModulePrivate();
};

//-----------------------------------------------------------------------------
// qSlicerVolumeTextureIDHelperModulePrivate methods

//-----------------------------------------------------------------------------
qSlicerVolumeTextureIDHelperModulePrivate::qSlicerVolumeTextureIDHelperModulePrivate()
{
}

//-----------------------------------------------------------------------------
// qSlicerVolumeTextureIDHelperModule methods

//-----------------------------------------------------------------------------
qSlicerVolumeTextureIDHelperModule::qSlicerVolumeTextureIDHelperModule(QObject* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerVolumeTextureIDHelperModulePrivate)
{
}

//-----------------------------------------------------------------------------
qSlicerVolumeTextureIDHelperModule::~qSlicerVolumeTextureIDHelperModule()
{
}

//-----------------------------------------------------------------------------
QString qSlicerVolumeTextureIDHelperModule::helpText() const
{
  return "This is a loadable module that can be bundled in an extension";
}

//-----------------------------------------------------------------------------
QString qSlicerVolumeTextureIDHelperModule::acknowledgementText() const
{
  return "This work was partially funded by NIH grant NXNNXXNNNNNN-NNXN";
}

//-----------------------------------------------------------------------------
QStringList qSlicerVolumeTextureIDHelperModule::contributors() const
{
  QStringList moduleContributors;
  moduleContributors << QString("John Doe (AnyWare Corp.)");
  return moduleContributors;
}

//-----------------------------------------------------------------------------
QIcon qSlicerVolumeTextureIDHelperModule::icon() const
{
  return QIcon(":/Icons/VolumeTextureIDHelper.png");
}

//-----------------------------------------------------------------------------
QStringList qSlicerVolumeTextureIDHelperModule::categories() const
{
  return QStringList() << "Examples";
}

//-----------------------------------------------------------------------------
QStringList qSlicerVolumeTextureIDHelperModule::dependencies() const
{
  return QStringList();
}

//-----------------------------------------------------------------------------
void qSlicerVolumeTextureIDHelperModule::setup()
{
  this->Superclass::setup();
}

//-----------------------------------------------------------------------------
qSlicerAbstractModuleRepresentation* qSlicerVolumeTextureIDHelperModule
::createWidgetRepresentation()
{
  return new qSlicerVolumeTextureIDHelperModuleWidget;
}

//-----------------------------------------------------------------------------
vtkMRMLAbstractLogic* qSlicerVolumeTextureIDHelperModule::createLogic()
{
  return vtkSlicerVolumeTextureIDHelperLogic::New();
}
