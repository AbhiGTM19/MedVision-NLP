import easyocr
import numpy as np
from PIL import Image
import io

class OCRService:
    def __init__(self):
        # Initialize the EasyOCR reader for English. 
        # By default it runs on GPU if available, falls back to CPU.
        self.reader = easyocr.Reader(['en'])

    def extract_text(self, image_bytes: bytes) -> str:
        """
        Takes raw image bytes, converts them to a format EasyOCR can read,
        and returns the extracted text string.
        """
        # Convert bytes to a PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert PIL Image to a numpy array (which EasyOCR expects)
        image_np = np.array(image)

        # Read text from image. detail=0 returns just the text strings.
        results = self.reader.readtext(image_np, detail=0)

        # Join the text blocks into a single cohesive string
        extracted_text = " ".join(results)
        return extracted_text

# Singleton instance to be used across the app
ocr_service = OCRService()
