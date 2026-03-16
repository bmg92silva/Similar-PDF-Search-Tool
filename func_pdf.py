from PIL import Image
import io
from torchvision import transforms
import pymupdf
import os
import os


def pdf_to_image(pdf_path, page_num=0, max_dimension=1000):
    """
    Convert a single PDF page to an image with max dimension constraint
   
    Args:
        pdf_path: Path to the PDF file
        page_num: Page number to convert (0-indexed)
        max_dimension: Maximum width or height in pixels (default: 1000)
       
    Returns:
        tuple: (image_bytes, filename) where image_bytes is PNG format and 
               filename is the name of the PDF file
    """
    # Open the PDF
    doc = pymupdf.open(pdf_path)
   
    # Get the specified page
    page = doc[page_num]
   
    # Get page dimensions
    page_rect = page.rect
    page_width = page_rect.width
    page_height = page_rect.height
   
    # Calculate zoom factor based on the larger dimension
    if page_width > page_height:
        zoom = max_dimension / page_width
    else:
        zoom = max_dimension / page_height
   
    # Create transformation matrix with zoom factor
    mat = pymupdf.Matrix(zoom, zoom)
   
    # Render page to a pixmap with the matrix applied
    pix = page.get_pixmap(matrix=mat)
   
    # Convert pixmap to bytes
    image_bytes = pix.tobytes("png")
   
    # Extract filename from path
    filename = os.path.basename(pdf_path)
   
    # Clean up
    doc.close()
   
    return image_bytes, filename


def pdf_Bytes_to_image(pdf_bytes, page_num=0, max_dimension=1000):
    """
    Convert a single PDF page to an image with max dimension constraint
   
    Args:
        pdf_bytes: PDF file content as bytes
        filename: Name of the PDF file (for return value)
        page_num: Page number to convert (0-indexed)
        max_dimension: Maximum width or height in pixels (default: 1000)
       
    Returns:
        tuple: (image_bytes, filename) where image_bytes is PNG format and 
               filename is the name of the PDF file
    """
    # Open the PDF from bytes
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
   
    # Get the specified page
    page = doc[page_num]
   
    # Get page dimensions
    page_rect = page.rect
    page_width = page_rect.width
    page_height = page_rect.height
   
    # Calculate zoom factor based on the larger dimension
    if page_width > page_height:
        zoom = max_dimension / page_width
    else:
        zoom = max_dimension / page_height
   
    # Create transformation matrix with zoom factor
    mat = pymupdf.Matrix(zoom, zoom)
   
    # Render page to a pixmap with the matrix applied
    pix = page.get_pixmap(matrix=mat)
   
    # Convert pixmap to bytes
    image_bytes = pix.tobytes("png")
   
    # Clean up
    doc.close()
   
    return image_bytes


import onnxruntime as ort
import numpy as np

def embedding_pipeline(image_bytes, model=None, transform=None):
    """
    Pipeline to generate embedding from image bytes using ONNX model
    
    Args:
        image_bytes: Image bytes from pdf_to_image function
        model: Pre-loaded ONNX session (optional)
        transform: Pre-loaded transform (optional)
    
    Returns:
        tuple: (embedding_bytes, resized_image_bytes, original_image)
    """
    # Load ONNX model if not provided
    if model is None:
        onnx_model_path = "./models/dinov2_int8.onnx"
        model = ort.InferenceSession(
            onnx_model_path,
            providers=['CPUExecutionProvider']
        )
    
    # Define transform if not provided
    if transform is None:
        transform = transforms.Compose([
            transforms.Resize((518, 518)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    # Load and prepare image
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Generate embedding
    image_tensor = transform(image).unsqueeze(0)
    
    # Convert to numpy array for ONNX
    image_numpy = image_tensor.numpy()
    
    # Get input name from the model
    input_name = model.get_inputs()[0].name
    
    # Run inference
    embedding = model.run(None, {input_name: image_numpy})[0]
    embedding_bytes = embedding.tobytes()
    
    # Resize image to 1/4th
    original_width, original_height = image.size
    new_width = original_width // 4
    new_height = original_height // 4
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
    
    # Convert resized image to bytes
    img_byte_arr = io.BytesIO()
    resized_image.save(img_byte_arr, format='PNG')
    resized_image_bytes = img_byte_arr.getvalue()
    
    return embedding_bytes, resized_image_bytes
