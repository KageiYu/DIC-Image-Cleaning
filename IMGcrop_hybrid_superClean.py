#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 29 09:21:14 2025

@author: yujiayi
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revised on Mon Dec 01 2025

@author: yujiayi (Revised)
"""
import cv2
import os
import sys

# Supported extensions
VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.gif')

def get_hybrid_roi(image_paths):
    """
    Calculates a Hybrid Crop Box:
    - TOP, LEFT, RIGHT: Uses INTERSECTION (Overlap) to aggressively clean black edges.
    - BOTTOM: Uses UNION (Max Extent) to preserve the curve apex.
    """
    # 1. Initialize for INTERSECTION (Aggressive Cleaning)
    # Start Low/Left at 0 and push them IN (increase)
    hybrid_min_x = 0  # Left
    hybrid_min_y = 0  # Top
    
    # Start Right at Infinity and push it IN (decrease)
    hybrid_max_x = float('inf') # Right

    # 2. Initialize for UNION (Apex Preservation)
    # Start Bottom at 0 and push it OUT (increase to find max depth)
    hybrid_max_y = 0  # Bottom
    
    found_any_contour = False
    total = len(image_paths)

    for i, path in enumerate(image_paths):
        print(f"\r  [Phase 1: Analysis] Scanning {i+1}/{total}...", end="")
        
        img = cv2.imread(path)
        if img is None: continue

        # Standard Pre-processing
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            found_any_contour = True
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)

            current_min_x = x
            current_min_y = y
            current_max_x = x + w
            current_max_y = y + h

            # --- HYBRID LOGIC ---

            # LEFT (Intersection): Shrink inwards (Max of Mins)
            if current_min_x > hybrid_min_x: hybrid_min_x = current_min_x
            
            # TOP (Intersection): Shrink downwards (Max of Mins)
            if current_min_y > hybrid_min_y: hybrid_min_y = current_min_y
            
            # RIGHT (Intersection): Shrink inwards (Min of Maxs)
            if current_max_x < hybrid_max_x: hybrid_max_x = current_max_x
            
            # BOTTOM (Union): Expand downwards (Max of Maxs) -> PRESERVES APEX
            if current_max_y > hybrid_max_y: hybrid_max_y = current_max_y

    print(" Done.")
    
    if not found_any_contour:
        return None

    # SAFETY CHECK: 
    if hybrid_min_x >= hybrid_max_x:
        print(f"\n  [ERROR] The sample moved left/right so much that there is no valid overlap width!")
        return None
    
    if hybrid_min_y >= hybrid_max_y:
        print(f"\n  [ERROR] Invalid height detected.")
        return None
        
    return (hybrid_min_x, hybrid_min_y, hybrid_max_x, hybrid_max_y)

def process_subfolder(src_folder, dst_folder):
    images = [f for f in sorted(os.listdir(src_folder)) if f.lower().endswith(VALID_EXTENSIONS)]
    
    if not images:
        print(f"  [Skipping] No images found in {os.path.basename(src_folder)}")
        return

    full_paths = [os.path.join(src_folder, f) for f in images]

    # --- Phase 1: Calculate Hybrid Box ---
    roi = get_hybrid_roi(full_paths)
    
    if not roi:
        print(f"  [Skipping] Could not determine a valid crop area for {os.path.basename(src_folder)}")
        return

    min_x, min_y, max_x, max_y = roi
    
    width = max_x - min_x
    height = max_y - min_y
    print(f"  [ROI Detected] x=[{min_x}:{max_x}], y=[{min_y}:{max_y}] (Size: {width}x{height})")
    print(f"  * Top/Sides cleaned aggressively. Bottom expanded for apex.")

    # --- Phase 2: Crop and Save ---
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)

    for i, filename in enumerate(images):
        print(f"\r  [Phase 2: Cropping] Saving {i+1}/{len(images)}...", end="")
        
        src_path = os.path.join(src_folder, filename)
        dst_path = os.path.join(dst_folder, filename)
        
        img = cv2.imread(src_path)
        if img is None: continue

        # Crop
        cropped_img = img[min_y:max_y, min_x:max_x]
        
        # Save
        cv2.imwrite(dst_path, cropped_img)
    
    print(" Done.\n")

def main_batch_processor():
    print("--- Smart Batch Crop: HYBRID LOGIC ---")
    print("1. Top/Left/Right: Intersection (Aggressive clean)")
    print("2. Bottom: Union (Conservative, keep curve apex)\n")
    
    # 1. Get Input
    root_input = input("Enter path to the folder: ").strip()
    root_input = root_input.strip('"').strip("'")

    if not os.path.isdir(root_input):
        print("Error: Directory not found.")
        return

    # 2. Inspect Content
    all_items = sorted(os.listdir(root_input))
    subfolders = [i for i in all_items if os.path.isdir(os.path.join(root_input, i))]
    images = [i for i in all_items if i.lower().endswith(VALID_EXTENSIONS)]

    # 3. Determine Output Path
    folder_name = os.path.basename(root_input.rstrip(os.sep))
    parent_dir = os.path.dirname(root_input.rstrip(os.sep))
    root_output = os.path.join(parent_dir, f"{folder_name}_SuperCleaned")

    # 4. Processing Logic
    if len(subfolders) > 0:
        # --- MODE A: Process Root containing Subfolders ---
        print(f"\n[Mode: Recursive] Found {len(subfolders)} subfolders.")
        print(f"Output container: {root_output}\n")
        
        if not os.path.exists(root_output):
            os.makedirs(root_output)

        for sub in subfolders:
            src_sub = os.path.join(root_input, sub)
            dst_sub = os.path.join(root_output, f"{sub}_cleaned")
            
            print(f"Processing Folder: {sub}...")
            process_subfolder(src_sub, dst_sub)
            
    elif len(images) > 0:
        # --- MODE B: Process Single Folder ---
        print(f"\n[Mode: Single Folder] Found {len(images)} images (no subfolders).")
        print(f"Output folder: {root_output}\n")
        
        process_subfolder(root_input, root_output)
        
    else:
        print("\n[Error] The folder seems empty or contains no supported images/subfolders.")
        return

    print("All processing complete.")
    print(f"Output located at: {root_output}")

if __name__ == "__main__":
    main_batch_processor()