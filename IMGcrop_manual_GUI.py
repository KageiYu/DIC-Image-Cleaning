#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revised on Mon Dec 01 2025

@author: yujiayi (Revised)
"""
# pip install opencv-python numpy
import cv2
import os
import numpy as np
import sys

# Supported extensions
VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.gif')

# Global variables for mouse callback
drawing = False
ix, iy = -1, -1
fx, fy = -1, -1
roi_selected = False
scale_factor = 1.0
single_w = 0  # Width of a single image (scaled)

def mouse_callback(event, x, y, flags, param):
    global drawing, ix, iy, fx, fy, roi_selected, single_w
    
    # Combined display image passed via param
    display_img = param['img']
    clone = display_img.copy()
    window_name = param['window_name']

    # Normalize x to always be relative to the single image width
    # This allows drawing on either the left or right image
    norm_x = x % single_w
    
    # Constrain y to image height
    h, w, _ = display_img.shape
    norm_y = max(0, min(y, h))

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = norm_x, norm_y
        roi_selected = False

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            # Draw rectangle on Left Image
            cv2.rectangle(clone, (ix, iy), (norm_x, norm_y), (0, 255, 0), 2)
            
            # Draw Mirror rectangle on Right Image
            cv2.rectangle(clone, (ix + single_w, iy), (norm_x + single_w, norm_y), (0, 255, 0), 2)
            
            cv2.imshow(window_name, clone)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        fx, fy = norm_x, norm_y
        roi_selected = True
        
        # Draw final rectangle on Left
        cv2.rectangle(clone, (ix, iy), (fx, fy), (0, 255, 0), 2)
        # Draw final Mirror on Right
        cv2.rectangle(clone, (ix + single_w, iy), (fx + single_w, fy), (0, 255, 0), 2)
        
        cv2.imshow(window_name, clone)

def resize_for_display(img_first, img_last, max_screen_width=1600):
    """
    Resizes images so the side-by-side view fits on a standard monitor.
    Returns the combined image and the scale factor used.
    """
    h, w = img_first.shape[:2]
    combined_width_raw = w * 2
    
    scale = 1.0
    if combined_width_raw > max_screen_width:
        scale = max_screen_width / combined_width_raw
    
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    rs_first = cv2.resize(img_first, (new_w, new_h))
    rs_last = cv2.resize(img_last, (new_w, new_h))
    
    # Concatenate side by side
    combined = np.hstack((rs_first, rs_last))
    
    return combined, scale, new_w

def get_roi_manually(image_paths):
    global scale_factor, single_w, roi_selected, ix, iy, fx, fy
    
    if len(image_paths) < 1:
        return None
        
    # Load First and Last images
    first_path = image_paths[0]
    last_path = image_paths[-1]
    
    img_first = cv2.imread(first_path)
    img_last = cv2.imread(last_path)
    
    if img_first is None or img_last is None:
        print("Error reading images.")
        return None

    # Resize for display
    combined_display, scale, w_scaled = resize_for_display(img_first, img_last)
    scale_factor = scale
    single_w = w_scaled
    
    window_name = "Select ROI - Space/Enter to Confirm, 'c' to Clear"
    cv2.namedWindow(window_name)
    
    # Pass combined image to callback via dictionary
    params = {'img': combined_display, 'window_name': window_name}
    cv2.setMouseCallback(window_name, mouse_callback, params)
    
    cv2.imshow(window_name, combined_display)
    
    print("\n--- Controls ---")
    print("  [Mouse Drag] : Draw Box (Draw on left or right, it mirrors automatically)")
    print("  [Space/Entr]: Confirm Selection")
    print("  [     c     ]: Clear Selection")
    print("  [     q     ]: Quit")
    
    final_roi = None

    while True:
        key = cv2.waitKey(1) & 0xFF
        
        # Space (32) or Enter (13)
        if key == 32 or key == 13:
            if roi_selected:
                # Calculate coordinates in ORIGINAL resolution
                x1 = int(min(ix, fx) / scale_factor)
                y1 = int(min(iy, fy) / scale_factor)
                x2 = int(max(ix, fx) / scale_factor)
                y2 = int(max(iy, fy) / scale_factor)
                
                # Sanity check
                if x2 > x1 and y2 > y1:
                    final_roi = (x1, y1, x2, y2)
                    break
                else:
                    print("Invalid selection (width or height is 0). Try again.")
            else:
                print("Please draw a box first.")

        # 'c' to clear
        elif key == ord('c'):
            roi_selected = False
            cv2.imshow(window_name, combined_display)
            print("Selection cleared.")

        # 'q' to quit
        elif key == ord('q'):
            print("Operation cancelled by user.")
            break
            
    cv2.destroyAllWindows()
    return final_roi

def main():
    print("--- Manual Batch Cropper with GUI ---")
    
    # 1. Get Input Folder
    input_path = input("Enter path to image folder: ").strip()
    input_path = input_path.strip('"').strip("'")
    
    if not os.path.isdir(input_path):
        print("Error: Directory not found.")
        return

    # 2. Get Images
    image_files = sorted([f for f in os.listdir(input_path) 
                          if f.lower().endswith(VALID_EXTENSIONS)])
    
    if not image_files:
        print("No images found.")
        return

    full_paths = [os.path.join(input_path, f) for f in image_files]

    # 3. Open GUI for Selection
    roi = get_roi_manually(full_paths)
    
    if roi is None:
        return

    x1, y1, x2, y2 = roi
    print(f"\nTarget Crop Region: x=[{x1}:{x2}], y=[{y1}:{y2}]")
    
    # 4. Setup Output Folder
    parent_dir = os.path.dirname(input_path.rstrip(os.sep))
    folder_name = os.path.basename(input_path.rstrip(os.sep))
    output_dir = os.path.join(parent_dir, f"{folder_name}_GUIcleaned")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 5. Process
    print(f"Processing {len(image_files)} images...")
    
    for i, filename in enumerate(image_files):
        print(f"\rSaving {i+1}/{len(image_files)}...", end="")
        
        img = cv2.imread(full_paths[i])
        if img is None: continue
        
        # Crop
        crop = img[y1:y2, x1:x2]
        
        # Save
        cv2.imwrite(os.path.join(output_dir, filename), crop)

    print(f"\nDone! Saved to: {output_dir}")

if __name__ == "__main__":
    main()