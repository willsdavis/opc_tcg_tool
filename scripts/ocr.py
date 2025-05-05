import os
import cv2
import argparse
import numpy as np
import re
from paddleocr import PaddleOCR

def extract_card_info(image_path):
    """
    Extract card name and set number using region-specific OCR
    
    Args:
        image_path: Path to the card image
    
    Returns:
        Dictionary with card name and set number
    """
    # Initialize PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    
    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image at {image_path}")
    
    height, width, _ = img.shape
    
    # Define regions of interest (ROI)
    # Adjust the card name region to the bottom-middle (but not too low)
    name_roi_top = int(height * 0.78)
    name_roi_bottom = int(height * 0.92)
    name_roi = img[name_roi_top:name_roi_bottom, int(width * 0.2):int(width * 0.8)]
    
    # Bottom right corner for set number
    set_roi = img[int(height * 0.85):height, int(width * 0.75):width]
    
    # Perform OCR on specific regions
    name_result = ocr.ocr(name_roi, cls=True)
    set_result = ocr.ocr(set_roi, cls=True)
    
    # Extract text from name region
    card_name = None
    name_confidence = 0
    if name_result[0]:
        for line in name_result[0]:
            text, confidence = line[1][0], line[1][1]
            # Look for longer text that's likely to be a name
            if len(text) > 3 and confidence > name_confidence:
                card_name = text
                name_confidence = confidence
    
    # Extract text from set region, focusing on finding numbers
    set_number = None
    if set_result[0]:
        # First try to find text containing digits
        for line in set_result[0]:
            text = line[1][0]
            # Look specifically for numbers in the text
            if any(char.isdigit() for char in text):
                # If we find a number, prioritize it
                set_number = text
                break
    
    # If no set number was found with digits, fall back to any text in that region
    if set_number is None and set_result[0]:
        set_number = set_result[0][0][1][0]
    
    # Full image OCR as backup
    full_result = ocr.ocr(img, cls=True)
    all_texts = []
    if full_result[0]:
        for line in full_result[0]:
            all_texts.append(line[1][0])
            
        # If still no card name or set number, look in full text
        if card_name is None:
            for line in full_result[0]:
                text, confidence = line[1][0], line[1][1]
                box = line[0]  # Bounding box coordinates
                box_center_y = sum(p[1] for p in box) / 4  # Average y-coordinate
                
                # Check if this text is in the bottom part of the image
                if box_center_y > height * 0.75:
                    # If in bottom area and looks like a name
                    if len(text) > 3 and "." in text:
                        card_name = text
                        break
    
    return {
        "card_name": card_name,
        "set_number": set_number,
        "all_detected_text": all_texts
    }

def visualize_regions(image_path):
    """
    Generate a visualization of the detected regions
    """
    img = cv2.imread(image_path)
    height, width, _ = img.shape
    
    # Draw rectangles for the ROIs
    # Card name region (green) - adjusted to lower middle
    cv2.rectangle(img, 
                 (int(width * 0.2), int(height * 0.78)), 
                 (int(width * 0.8), int(height * 0.92)), 
                 (0, 255, 0), 2)
    
    # Set number region (blue) - bottom right corner
    cv2.rectangle(img, 
                 (int(width * 0.75), int(height * 0.85)), 
                 (width, height), 
                 (255, 0, 0), 2)
    
    output_path = "card_regions.jpg"
    cv2.imwrite(output_path, img)
    print(f"Visualization saved to {output_path}")
    
    return output_path

def process_batch(directory, output_file=None):
    """
    Process all image files in a directory
    
    Args:
        directory: Directory containing images
        output_file: Path to save results (optional)
    
    Returns:
        List of results
    """
    supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    results = []
    
    # Initialize output file if provided
    if output_file:
        with open(output_file, 'w') as f:
            f.write("Image,Card Name,Set Number\n")
    
    # Get all image files in the directory
    for filename in os.listdir(directory):
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in supported_formats:
            image_path = os.path.join(directory, filename)
            
            try:
                print(f"Processing {filename}...")
                card_info = extract_card_info(image_path)
                
                # Print result to console
                print(f"  Card Name: {card_info['card_name']}")
                print(f"  Set Number: {card_info['set_number']}")
                
                # Store result
                result = {
                    "image": filename,
                    "card_name": card_info['card_name'],
                    "set_number": card_info['set_number']
                }
                results.append(result)
                
                # Write to output file if provided
                if output_file:
                    with open(output_file, 'a') as f:
                        f.write(f"{filename},{card_info['card_name'] or 'N/A'},{card_info['set_number'] or 'N/A'}\n")
            
            except Exception as e:
                print(f"  Error processing {filename}: {e}")
    
    if output_file:
        print(f"\nResults saved to {output_file}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Extract card information using targeted OCR')
    parser.add_argument('input', type=str, help='Path to the card image or directory of images')
    parser.add_argument('--batch', action='store_true', help='Process a directory of images')
    parser.add_argument('--output', type=str, help='Output file for batch processing results')
    parser.add_argument('--debug', action='store_true', help='Print all detected text')
    parser.add_argument('--visualize', action='store_true', help='Create visualization of regions')
    
    args = parser.parse_args()
    
    try:
        if args.batch:
            if not os.path.isdir(args.input):
                raise ValueError(f"{args.input} is not a directory")
            
            process_batch(args.input, args.output)
        else:
            if args.visualize:
                visualize_regions(args.input)
                
            card_info = extract_card_info(args.input)
            
            print("\n===== Card Information =====")
            print(f"Card Name: {card_info['card_name']}")
            print(f"Set Number: {card_info['set_number']}")
            
            if args.debug:
                print("\n===== All Detected Text =====")
                for i, text in enumerate(card_info['all_detected_text']):
                    print(f"{i+1}. {text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()