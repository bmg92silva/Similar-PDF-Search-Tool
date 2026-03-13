# Similar PDF Search Tool

A desktop application for finding visually similar PDF documents using AI-powered image embeddings and cosine similarity matching.

## Features

- **Visual PDF Similarity Search**: Find PDFs that are visually similar using deep learning embeddings
- **PyQt5 GUI**: Graphical interface for interaction
- **DINOv2 Model**: DINOv2 small for image embeddings
- **Local Database**: Store and manage PDF embeddings locally with SQLite
- **Customizable Settings**: Configure database paths, number of results, and search parameters
- **Batch Processing**: Process multiple PDFs and build embeddings for your collection
- **Similarity Scoring**: Get cosine similarity scores to understand how similar documents are

## Project Structure

```
├── main.py                  # Application entry point
├── main_window.py           # Main window controller
├── main_window.ui           # Qt Designer UI file
├── card.ui                  # Card UI component
├── func_pdf.py              # PDF processing utilities
├── func_similar.py          # Similarity calculation functions
├── func_db.py               # Database operations
├── func_json.py             # Settings/JSON handling
├── func_ui.py               # UI-related functions
├── settings.json            # Application settings
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Project configuration
├── models/
│   └── dinov2_int8.onnx     # Quantized DINOv2 model
```

## Prerequisites

- Python 3.12 or higher
- Windows, macOS, or Linux

## Installation

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv
.\venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
python main.py
```

The application will:
1. Create a `settings.json` file if it doesn't exist
2. Initialize a local database for storing embeddings
3. Display the main window with the UI

### How It Works

1. **Load PDF Files**: Select PDF files from your system
2. **Generate Embeddings**: The tool uses DINOv2 to convert the first page of each PDF to an embedding vector
3. **Store Embeddings**: Embeddings are stored in a local SQLite database
4. **Search**: Upload or select a query PDF to find similar documents
5. **View Results**: Get ranked results with similarity scores

## Configuration

Settings are stored in `settings.json`:

```json
{
  "use_custom_path": false,
  "custom_db_path": "Not set",
  "num_results": 10
}
```

- **use_custom_path**: Whether to use a custom database location
- **custom_db_path**: Custom path to store the database
- **num_results**: Number of similar results to return

## Key Components

### PDF Processing (`func_pdf.py`)
- Converts PDF pages to images
- Handles dimension constraints for consistent processing
- Supports multi-page PDFs

### Similarity Calculation (`func_similar.py`)
- Normalizes embeddings
- Calculates cosine similarity scores
- Ranks results by similarity

### Database Operations (`func_db.py`)
- Manages SQLite database
- Stores and retrieves embeddings
- Handles database initialization

### Settings Management (`func_json.py`)
- Handles application configuration
- Manages persistent settings

## Dependencies

- **PyQt5**: GUI framework
- **torch**: Deep learning framework
- **torchvision**: Computer vision utilities
- **PyMuPDF**: PDF processing
- **onnxruntime**: ONNX model inference
- **numpy**: Numerical computations
- **pandas**: Data manipulation

See `requirements.txt` for the complete dependency list.

## Model

The application uses **DINOv2 (int8 quantized)** for generating embeddings:
- Quantized to 8-bit for reduced memory usage
- Provides robust visual embeddings
- Based on Vision Transformer architecture

## Troubleshooting

### Database Issues
If you encounter database errors, delete the existing database and the application will create a new one on the next startup.

### Model Not Found
Ensure the `models/dinov2_int8.onnx` file is present in the models directory.

### Settings Issues
Delete `settings.json` to reset to default settings.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Support

If you have any questions or need help, please open an issue on GitHub.
