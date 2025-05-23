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

#ifndef __qSlicerVolumeTextureIDHelperModuleWidget_h
#define __qSlicerVolumeTextureIDHelperModuleWidget_h

// Slicer includes
#include "qSlicerAbstractModuleWidget.h"

#include "qSlicerVolumeTextureIDHelperModuleExport.h"

class qSlicerVolumeTextureIDHelperModuleWidgetPrivate;
class vtkMRMLNode;

class Q_SLICER_QTMODULES_VOLUMETEXTUREIDHELPER_EXPORT qSlicerVolumeTextureIDHelperModuleWidget :
  public qSlicerAbstractModuleWidget
{
  Q_OBJECT

public:

  typedef qSlicerAbstractModuleWidget Superclass;
  qSlicerVolumeTextureIDHelperModuleWidget(QWidget *parent=0);
  virtual ~qSlicerVolumeTextureIDHelperModuleWidget();

public slots:


protected:
  QScopedPointer<qSlicerVolumeTextureIDHelperModuleWidgetPrivate> d_ptr;

  void setup() override;

private:
  Q_DECLARE_PRIVATE(qSlicerVolumeTextureIDHelperModuleWidget);
  Q_DISABLE_COPY(qSlicerVolumeTextureIDHelperModuleWidget);
};

#endif
