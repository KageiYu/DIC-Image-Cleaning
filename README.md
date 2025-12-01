
# Image Cleaning Toolkit for Bending Polymer Films

## Overview

This repository contains a set of Python scripts designed to prepare raw microscope/camera images of polymer films for Machine Learning (ML) training and Digital Image Correlation (DIC).

The primary goal of these tools is to **remove useless black backgrounds** while ensuring that critical material data (specifically the **film edges** and **bending apex**) are preserved across the entire time-series experiment.

## Requirements

  * Python 3.x
  * OpenCV (`opencv-python`)
  * NumPy (`numpy`)

<!-- end list -->

```bash
pip install opencv-python numpy
```

-----

## 1\. `IMGcrop_union_rough.py` (The Conservative Approach)

### Logic & Function

This script calculates the **"Maximum Envelope"** (Union) of the film's movement across all images in a sequence.

1.  **Pass 1 (Analysis):** It scans every image to find the film's bounding box.
2.  **Calculation:** It finds the *left-most*, *right-most*, *highest*, and *lowest* pixels the film **ever** touched during the experiment.
3.  **Pass 2 (Cropping):** It applies this single "Super Bounding Box" to all images.

### Best For

  * **Large Deformation Tests:** When the sample moves or bends significantly.
  * **Safety First:** When you absolutely cannot risk cutting off any part of the sample, even if it means keeping some black background in the early frames.

### Pros & Cons

  * ✅ **Safe:** Guarantees the film (and its apex) is never cut off.
  * ✅ **Stable:** Keeps the coordinate system consistent for DIC.
  * ⚠️ **Noise:** Will retain black background in frames where the film is flat/undeformed.
<img width="1466" height="762" alt="union" src="https://github.com/user-attachments/assets/c90dd469-7d26-4fe2-909b-ef5fa0f4b1d6" />

-----

## 2\. `IMGcrop_hybrid_superClean.py` (The Optimized Approach)

### Logic & Function

This script uses a **"Best of Both Worlds"** logic to maximize image data density. It treats the bottom edge differently from the other three sides.

1.  **Top, Left, Right (Intersection Logic):** It finds the *inner-most* common edge. It effectively "squeezes" the crop window inward to remove black drift caused by camera vibration or minor sample shifting.
2.  **Bottom (Union Logic):** It finds the *lowest* point the film ever reaches. It expands the crop window downward to capture the maximum deflection (the curve apex).

### Best For

  * **Machine Learning Datasets:** Creates the cleanest possible images with the least amount of "dead" black pixels, optimizing training efficiency.
  * **Bending Tests:** specifically designed to handle films that start flat and bend downwards.

### Pros & Cons

  * ✅ **Clean:** Removes black edges from the top and sides aggressively.
  * ✅ **Apex-Safe:** Preserves the downward bending curve.
  * ⚠️ **Risk:** If the sample drifts significantly to the left/right, the "Intersection" logic might slice off a small sliver of the static film edge.

<img width="1452" height="755" alt="hybrid" src="https://github.com/user-attachments/assets/403a6977-7ce1-4c3c-9c2a-8fffcaf1bdd2" />

-----

## 3\. `IMGcrop_manual_GUI.py` (The Human-in-the-Loop)

### Logic & Function

A graphical interface that gives the user total control over the cropping window.

1.  **Visualization:** Opens the **First** (t=0) and **Last** (t=end) images of the sequence side-by-side.
2.  **Synchronization:** Drawing a box on one image automatically mirrors it on the other. This allows you to visually verify that your crop includes the film in both its initial (flat) and final (bent) states.
3.  **Batch Processing:** Once confirmed, it applies these specific coordinates to every image in the folder.

### Best For

  * **Difficult Lighting:** When the automatic thresholding (Otsu's method) fails due to glare, low contrast, or artifacts.
  * **Specific ROI:** When you only want to analyze a specific section of the film (e.g., the center 50%) and ignore the clamps/edges.

### Controls

  * **Mouse Drag:** Draw rectangle (works on left or right image).
  * **Space / Enter:** Confirm selection and start processing.
  * **C:** Clear selection.
  * **Q:** Quit without saving.

-----

## Usage Guide
**Please see the demo video.**
1.  **Organize your data:** Put your raw images inside subfolders within a root directory.
    ```text
    /My_Experiment_Root
    ├── /Sample_A_Run1
    ├── /Sample_A_Run2

    /Sample_B_4GUI
    ```
    ```text
    Result:

    /My_Experiment_Root_SuperCleaned
    ├── /Sample_A_Run1_cleaned
    ├── /Sample_A_Run2_cleaned

    /My_Experiment_Root_union_cropped
    ├── /Sample_A_Run1_cropped
    ├── /Sample_A_Run2_cropped

    /Sample_B_4GUI_cleaned
    ```
2.  **Run the script:**
    ```bash
    python3 IMGcrop_union_rough.py
    ```
3.  **Input Path:** Paste the path to `My_Experiment_Root`.
4.  **Output:** A new folder `My_Experiment_Root_cleaned` will be created automatically.
