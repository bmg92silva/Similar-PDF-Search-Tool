from PyQt5 import uic
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QPixmap, QDesktopServices, QImage
from PyQt5.QtWidgets import QWidget, QGridLayout, QMessageBox
from PIL import Image
import io

from func_db import delete_record_by_material_code

def create_result_card(material_code, similarity, image_blob):
    """Create a result card widget by loading UI template and populating with data"""

    # Load the UI template
    card = uic.loadUi('card.ui')
    
    # Set material code
    card.materialLabel.setText(f"<b>{material_code}</b>")
    
    # Set similarity with color coding
    card.similarityLabel.setText(f"Similarity: {similarity:.4f}")

    # Handle image with aspect ratio preservation
    max_width = 275
    max_height = 280
    pil_image = fit_image(image_blob, max_width, max_height)
    
    # Convert PIL Image to QPixmap
    data = pil_image.tobytes("raw", "RGBA")
    qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGBA8888)
    pixmap = QPixmap.fromImage(qimage)

    # Set image
    card.imageLabel.setFixedSize(max_width, max_height)
    card.imageLabel.setPixmap(pixmap)
    
    # Connect button signals
    def delete_record():
        reply = QMessageBox.question(
            card,
            'Confirm Delete',
            f'Are you sure you want to delete record {material_code}?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_record_by_material_code(material_code)
            # Emit signal to refresh UI if needed
    
    card.deleteButton.clicked.connect(delete_record)
    
    return card


def fit_image(image_blob, max_width, max_height):
    # Open the original image
    img = Image.open(io.BytesIO(image_blob))
    
    # Calculate the aspect ratio and resize to fit within max dimensions
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    
    # Create a new transparent canvas with exact max dimensions
    # Use 'RGBA' mode for transparency
    new_img = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))
    
    # Calculate position to center the image
    paste_x = (max_width - img.width) // 2
    paste_y = (max_height - img.height) // 2
    
    # Paste the resized image onto the transparent canvas
    new_img.paste(img, (paste_x, paste_y))
    
    return new_img


def populate_results_scroll_area(resultsScrollArea, results):
    """
    Populate the scroll area with result cards in a 4-column grid
    
    Args:
        resultsScrollArea: QScrollArea widget with 970px fixed width
        results: List of tuples (material_code, similarity, image_blob)
    """
    # Create container widget
    container = QWidget()
    
    # Create grid layout
    grid_layout = QGridLayout(container)
    grid_layout.setSpacing(10)
    grid_layout.setContentsMargins(10, 10, 10, 10)
    
    # Add cards to grid (4 per row)
    for index, (material_code, similarity, image_blob) in enumerate(results):
        row = index // 3
        col = index % 3
        
        card = create_result_card(material_code, similarity, image_blob)
        grid_layout.addWidget(card, row, col)
    
    # Set fixed column stretch (prevents columns from expanding)
    for col in range(3):
        grid_layout.setColumnStretch(col, 0)
    
    # Set the container as the scroll area's widget
    resultsScrollArea.setWidget(container)
    resultsScrollArea.setWidgetResizable(True)
    resultsScrollArea.setFixedWidth(970)


# Usage example:
# results = func_similar.find_similar_pipeline(embedding_bytes, top_k=12)
# populate_results_scroll_area(resultsScrollArea, results)


