# AnatomyCarve

AnatomyCarve is a module that allows interactive visualization of 3D medical images by enabling users to perform clipping on segments of their choice. This customized carving of the dataset enables the creation of detailed visualizations similar to those found in anatomical textbooks.

![Screenshot 2025-06-26 153232](https://github.com/user-attachments/assets/df90204b-5d21-4226-b2b4-e3da5c3012b1)

# Modules

- AnatomyCarve: The main module that presents a user interface to select images, insert a sphere in the scene, and then select which segments should be clipped.

# Prerequisites

- Windows or Linux operating system.
- GPU that supports OpenGL 4.3 or newer.

# Tutorial

1. Install the AnatomyCarve module from the Extensions Manager in 3D Slicer. Restart 3D Slicer.
2. Press on the "Download Sample Data" button, and click on the following datasets:
    - CTA abdomen (Panoramix)
    - CTA abdomen (Panoramix) segmentation

3. Go to Modules => Rendering => AnatomyCarve.
4. In the "Intensity volume" field, select "Panormix-cropped".
5. In the "Segmentation" field, select "Panoramix-cropped_Segmentation".
6. In the "View" field, select "View1".
7. Click on the "Render" button.
8. Scroll way down in the list of segments, and click on the visibility icon (the small eye at left column of each segment) for the following three segments:
    - subcutaneous_fat
    - torso_fat
    - muscle
9. Rotate the 3D view of main view by clicking on it and dragging the mouse. You will see that an invisible sphere was added into the image and it clips the three segments that were deselected previously.

# For Developers

In addition to the main volume node, a helper module VolumeTextureIdHelper is present that exposes some internal OpenGL data that is accessed by the main AnatomyCarve module.
