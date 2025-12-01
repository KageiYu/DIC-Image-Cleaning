#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revised on Mon Dec 01 2025

@author: yujiayi (Revised)
"""
# pip install opencv-python numpy
import cv2
import os
import sys

# Supported extensions
VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.gif')

def get_union_roi(image_paths):
    """
    Phase 1: Analyzes all images in a list to find the 
    maximum extents (Super Bounding Box) of the polymer film.
    """
    global_min_x = float('inf')
    global_min_y = float('inf')
    global_max_x = 0
    global_max_y = 0
    
    found_any_contour = False

    total = len(image_paths)
    for i, path in enumerate(image_paths):
        # Progress indicator for Phase 1
        print(f"\r    [Phase 1: Analysis] Scanning {i+1}/{total}...", end="")
        
        img = cv2.imread(path)
        if img is None: continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Otsu's thresholding
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            found_any_contour = True
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)

            # Update Global Extremes
            if x < global_min_x: global_min_x = x
            if y < global_min_y: global_min_y = y
            if (x + w) > global_max_x: global_max_x = x + w
            if (y + h) > global_max_y: global_max_y = y + h

    print(" Done.")
    
    if not found_any_contour:
        return None
        
    return (global_min_x, global_min_y, global_max_x, global_max_y)

def process_single_folder(src_folder, dst_folder):
    """
    Handles the logic for a single folder of images.
    """
    # Gather images
    images = [f for f in sorted(os.listdir(src_folder)) if f.lower().endswith(VALID_EXTENSIONS)]
    
    if not images:
        print(f"  [Skipping] No images found in {os.path.basename(src_folder)}")
        return

    full_paths = [os.path.join(src_folder, f) for f in images]

    # --- Phase 1: Calculate Union Box ---
    roi = get_union_roi(full_paths)
    
    if not roi:
        print(f"  [Warning] Could not detect any objects in {os.path.basename(src_folder)}")
        return

    min_x, min_y, max_x, max_y = roi
    print(f"    [ROI Detected] x=[{min_x}:{max_x}], y=[{min_y}:{max_y}]")

    # --- Phase 2: Crop and Save ---
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)

    for i, filename in enumerate(images):
        print(f"\r    [Phase 2: Cropping] Saving {i+1}/{len(images)}...", end="")
        
        src_path = os.path.join(src_folder, filename)
        dst_path = os.path.join(dst_folder, filename)
        
        img = cv2.imread(src_path)
        if img is None: continue

        # Crop
        cropped_img = img[min_y:max_y, min_x:max_x]
        
        # Save
        cv2.imwrite(dst_path, cropped_img)
    
    print(" Done.\n")

def main_smart_processor():
    print("--- Image Crop by Union ROI ---")
    print("Logic: Detects if input is a Root folder (multiple subfolders) or a Direct folder (images only).")
    print("Calculates 'Super Bounding Box' to ensure film is never cropped out.\n")
   
    # 1. Get Input
    raw_input = input("Enter path to the folder: ").strip()
    # Remove quotes and trailing slashes for consistency
    input_path = raw_input.strip('"').strip("'").rstrip(os.sep)

    if not os.path.isdir(input_path):
        print("Error: Directory not found.")
        return

    # 2. Analyze Directory Contents
    items = os.listdir(input_path)
    
    # Check for Subdirectories
    subfolders = [i for i in items if os.path.isdir(os.path.join(input_path, i))]
    
    # Check for Images
    images = [i for i in items if i.lower().endswith(VALID_EXTENSIONS)]

    # 3. Decision Logic
    if len(subfolders) > 0:
        # --- SCENARIO A: Root Folder containing Subfolders ---
        print(f"\n[Mode: Root Directory] Found {len(subfolders)} subfolders.")
        
        base_name = os.path.basename(input_path)
        root_output = os.path.join(os.path.dirname(input_path), f"{base_name}_union_cropped")
        
        if not os.path.exists(root_output):
            os.makedirs(root_output)
            print(f"Output Root Created: {root_output}\n")

        for sub in subfolders:
            src_sub = os.path.join(input_path, sub)
            dst_sub = os.path.join(root_output, f"{sub}_cropped") 
            
            print(f"Processing Subfolder: {sub}")
            process_single_folder(src_sub, dst_sub)
            
        print(f"All subfolders processed. Output: {root_output}")

    elif len(images) > 0:
        # --- SCENARIO B: Single Folder containing Images ---
        print(f"\n[Mode: Direct Folder] Found {len(images)} images.")
        
        base_name = os.path.basename(input_path)
        dst_folder = os.path.join(os.path.dirname(input_path), f"{base_name}_cleaned")
        
        print(f"Processing Folder: {base_name}")
        process_single_folder(input_path, dst_folder)
        
        print(f"Processing complete. Output: {dst_folder}")

    else:
        print("Error: The selected folder contains no images and no subfolders.")

if __name__ == "__main__":
    main_smart_processor()