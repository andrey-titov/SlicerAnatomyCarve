# AnatomyCarve

AnatomyCarve is a 3D Slicer module that allows interactive visualization of 3D medical images by enabling users to perform clipping on segments of their choice. This customized carving of the dataset enables the creation of detailed visualizations similar to those found in anatomical textbooks.

<img width="2556" height="1289" alt="Screenshot 2025-07-16 170326" src="https://github.com/user-attachments/assets/95592713-5956-45b5-a00d-c834633021c0" />


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
4. Click on the "Render" button.
5. Scroll way down in the list of segments, and click on the visibility icon (the small eye at left column of each segment) for the following three segments:
    - subcutaneous_fat
    - torso_fat
    - muscle
6. Rotate the 3D view of main view by clicking on it and dragging the mouse. You will see that an invisible sphere was added into the image and it clips the three segments that were deselected previously.
7. Press on the "Place a control point" button in the "Clipping spheres" table.
8. Drag your mouse on the 3D view and click anywhere in the 3D view close to the volume. A new clipping sphere will be positioned in the 3D view.
9. Press on the small "closed eye" icon next to "muscle" segment in the list of segments to transform it into an "open eye" icon. As a result, the second sphere won't clip the "muscle" segment, but it will still clip the "subcutaneous_fat" and "torso_fat" segments.
10. Drag the "sphere radius" slider widget to change the radius of the last added clipping sphere. You should see the clipping update for the "subcutaneous_fat" and "torso_fat" segments.

# For Developers

In addition to the main volume node, a helper module VolumeTextureIdHelper is present that exposes some internal OpenGL data that is accessed by the main AnatomyCarve module.

# References
[AnatomyCarve: A VR occlusion management technique for medical images based on segment-aware clipping](https://arxiv.org/abs/2507.05572)
