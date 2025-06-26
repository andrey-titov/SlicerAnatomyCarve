# AnatomyCarve

AnatomyCarve is a module that allows interactive visualization of 3D medical images by enabling users to perform clipping on segments of their choice. This customized carving of the dataset enables the creation of detailed visualizations similar to those found in anatomical textbooks.

![Screenshot 2025-06-26 153232](https://github.com/user-attachments/assets/df90204b-5d21-4226-b2b4-e3da5c3012b1)

# Sub-Modules

- AnatomyCarve: The main module that presents a user interface to select images, insert a sphere in the scene, and then select which segments should be clipped.
- VolumeTextureIdHelper: A helper module that exposes some internal OpenGL data to be accessed by the main AnatomyCarve module.
