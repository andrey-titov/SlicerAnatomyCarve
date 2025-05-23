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

#ifndef __qSlicerVolumeTextureIDHelperFooBarWidget_h
#define __qSlicerVolumeTextureIDHelperFooBarWidget_h

// Qt includes
#include <QWidget>

// FooBar Widgets includes
#include "qSlicerVolumeTextureIDHelperModuleWidgetsExport.h"

class qSlicerVolumeTextureIDHelperFooBarWidgetPrivate;

class Q_SLICER_MODULE_VOLUMETEXTUREIDHELPER_WIDGETS_EXPORT qSlicerVolumeTextureIDHelperFooBarWidget
  : public QWidget
{
  Q_OBJECT
public:
  typedef QWidget Superclass;
  qSlicerVolumeTextureIDHelperFooBarWidget(QWidget *parent=0);
  ~qSlicerVolumeTextureIDHelperFooBarWidget() override;

protected slots:

protected:
  QScopedPointer<qSlicerVolumeTextureIDHelperFooBarWidgetPrivate> d_ptr;

private:
  Q_DECLARE_PRIVATE(qSlicerVolumeTextureIDHelperFooBarWidget);
  Q_DISABLE_COPY(qSlicerVolumeTextureIDHelperFooBarWidget);
};

#endif
