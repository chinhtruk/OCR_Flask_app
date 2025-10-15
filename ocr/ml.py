"""
The AI model that will take an image as an input and give a str type output of the text on the image
"""

import pytesseract
import numpy as np 
from PIL import Image
import os

# Specify the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

def extract_text(image_path) -> str:
    try:
        # Validate file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        # Validate file is an image
        try:
            image = Image.open(image_path)
            image.verify()  # Verify it's actually an image
        except Exception:
            raise ValueError("Invalid image file")
            
        # Reopen image after verify (verify closes the image)
        image = Image.open(image_path)
        
        # Use Vietnamese language for OCR
        text = pytesseract.image_to_string(image, lang='vie')
        
        # Remove symbols and clean up text
        characters_to_remove = "!()@*>+-/,'|£#%$&^_~"
        text = ''.join(char for char in text if char not in characters_to_remove)
        
        # Remove empty lines and join with newlines
        text_lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(text_lines)
        
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")

# Example usage
# image_path = 'my_code/flask-app/sample_data/img.png'
# extracted_text = extract_text(image_path)
# print("Extracted Text:", extracted_text)




