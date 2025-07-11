#-----------------------------------------------------------------------------
set(MODULE_NAME AnatomyCarve)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  AnatomyCarveLogic/__init__.py
  AnatomyCarveLogic/AnatomyCarveLogic.py
  AnatomyCarveLogic/ComputeShader.py
  AnatomyCarveLogic/Texture.py
  AnatomyCarveLogic/Context.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/Icons/Panoramix-cropped-segmentation.png
  Resources/UI/${MODULE_NAME}.ui
  Resources/Shaders/Test.comp
  Resources/Shaders/FillColorVolume.comp
  Resources/Shaders/Noise.comp
  Resources/Shaders/DilateColorVolume.comp
  Resources/Shaders/CarveVoxels.comp
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
