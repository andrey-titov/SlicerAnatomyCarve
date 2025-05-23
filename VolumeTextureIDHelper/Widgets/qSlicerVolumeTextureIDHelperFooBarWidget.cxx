/*==============================================================================

  Program: 3D Slicer

  Copyright (c) Kitware Inc.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
  and was partially funded by NIH grant 3P41RR013218-12S1

==============================================================================*/

// FooBar Widgets includes
#include "qSlicerVolumeTextureIDHelperFooBarWidget.h"
#include "ui_qSlicerVolumeTextureIDHelperFooBarWidget.h"

//-----------------------------------------------------------------------------
class qSlicerVolumeTextureIDHelperFooBarWidgetPrivate
  : public Ui_qSlicerVolumeTextureIDHelperFooBarWidget
{
  Q_DECLARE_PUBLIC(qSlicerVolumeTextureIDHelperFooBarWidget);
protected:
  qSlicerVolumeTextureIDHelperFooBarWidget* const q_ptr;

public:
  qSlicerVolumeTextureIDHelperFooBarWidgetPrivate(
    qSlicerVolumeTextureIDHelperFooBarWidget& object);
  virtual void setupUi(qSlicerVolumeTextureIDHelperFooBarWidget*);
};

// --------------------------------------------------------------------------
qSlicerVolumeTextureIDHelperFooBarWidgetPrivate
::qSlicerVolumeTextureIDHelperFooBarWidgetPrivate(
  qSlicerVolumeTextureIDHelperFooBarWidget& object)
  : q_ptr(&object)
{
}

// --------------------------------------------------------------------------
void qSlicerVolumeTextureIDHelperFooBarWidgetPrivate
::setupUi(qSlicerVolumeTextureIDHelperFooBarWidget* widget)
{
  this->Ui_qSlicerVolumeTextureIDHelperFooBarWidget::setupUi(widget);
}

//-----------------------------------------------------------------------------
// qSlicerVolumeTextureIDHelperFooBarWidget methods

//-----------------------------------------------------------------------------
qSlicerVolumeTextureIDHelperFooBarWidget
::qSlicerVolumeTextureIDHelperFooBarWidget(QWidget* parentWidget)
  : Superclass( parentWidget )
  , d_ptr( new qSlicerVolumeTextureIDHelperFooBarWidgetPrivate(*this) )
{
  Q_D(qSlicerVolumeTextureIDHelperFooBarWidget);
  d->setupUi(this);
}

//-----------------------------------------------------------------------------
qSlicerVolumeTextureIDHelperFooBarWidget
::~qSlicerVolumeTextureIDHelperFooBarWidget()
{
}
