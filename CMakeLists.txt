cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(AnatomyCarve)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/andrey-titov/SlicerAnatomyCarve")
set(EXTENSION_CONTRIBUTORS "Andrey Titov (Ecole de Technologie Superieure), Liam O'Connor (Concordia University)")
set(EXTENSION_DESCRIPTION "AnatomyCarve is a module that allows interactive visualization of 3D medical images by enabling users to perform clipping on segments of their choice. This customized carving of the dataset enables the creation of detailed visualizations similar to those found in anatomical textbooks.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/andrey-titov/SlicerAnatomyCarve/main/AnatomyCarve/Resources/Icons/AnatomyCarve.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/andrey-titov/SlicerAnatomyCarve/main/docs/Screenshot%202025-06-26%20153232.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(AnatomyCarve)
add_subdirectory(VolumeTextureIDHelper)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
