import sqlite3
import pandas as pd
import os
import func_json


def get_db_path():
    """Determine the database path based on current settings"""
    saved_settings = func_json.load_settings()
    use_custom = saved_settings['use_custom_path']
    custom_db_path = saved_settings['custom_db_path']
    
    # Define default path
    default_path = os.path.dirname(os.path.abspath(__file__))
    
    # Apply custom path setting with fallback logic
    default_path_exists = os.path.exists(default_path)
    
    if default_path_exists:
        # Default path exists, use normal logic
        if custom_db_path != "Not set" and custom_db_path != "" and use_custom == True:
            db_path = os.path.join(custom_db_path, 'data.db')
        else:
            db_path = os.path.join(default_path, 'data.db')
    else:
        # Default path doesn't exist, activate custom path or use app directory
        if custom_db_path and custom_db_path != "Not set" and os.path.exists(custom_db_path):
            # Use existing custom path
            db_path = os.path.join(custom_db_path, 'data.db')
            print(f"✓ Using custom path (default path not found): {custom_db_path}")
        else:
            # Use app directory as fallback
            app_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(app_dir, 'data.db')
            print(f"⚠️ Default path not found. Using app directory as fallback: {app_dir}")
    
    return db_path


db_path = get_db_path()


def initialize_database():
    """Initialize database if it doesn't exist"""
    if not os.path.exists(db_path):
        print(f"Database not found. Creating new database at: {db_path}")
        create_db()
        return (f"Database created successfully at: {db_path}")
    else:
        return (f"Database already exists at: {db_path}")


def create_db():
    """Create SQLite database for PDF embeddings and orders"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_code INTEGER NOT NULL UNIQUE,
            embedding BLOB NOT NULL,
            image_blob BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def insert_pdf_row(filename, embedding_bytes, resized_image_bytes):
    """
    Insert PDF data into database
    
    Args:
        db_path: Path to SQLite database
        filename: Original filename
        embedding_bytes: Pre-generated embedding bytes
        resized_image_bytes: Pre-processed resized image bytes
    
    Returns:
        Row ID of inserted record
    """
    # Get first 9 characters of filename
    short_filename = filename
    
    # Insert into database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO embeddings (material_code, embedding, image_blob)
        VALUES (?, ?, ?)
    """, (short_filename, embedding_bytes, resized_image_bytes))
    
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return row_id


def material_code_exists(material_code):
    """Check if material_code already exists in embeddings table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT 1 FROM embeddings WHERE material_code = ? LIMIT 1',
        (material_code,)
    )
    
    exists = cursor.fetchone() is not None
    conn.close()
    
    return exists


def fetch_embeddings_from_db():
    """
    Retrieve all embeddings, material codes, and images from database.
    
    Parameters:
    -----------
    db_path : str
        Path to the SQLite database
    
    Returns:
    --------
    list of tuples
        List of (material_code, embedding_blob, image_blob)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT material_code, embedding, image_blob FROM embeddings")
    rows = cursor.fetchall()
    
    conn.close()
    return rows



def count_po():
    """
    Return the count of purchase orders (no longer used as price functionality removed)
    
    Returns:
        0 (price table no longer exists)
    """
    return 0


def delete_record_by_material_code(material_code):
    """
    Delete a record from the embeddings table by material_code.
    
    Parameters:
    -----------
    db_path : str
        Path to the SQLite database file
    material_code : int
        The material code of the record to delete
    
    Returns:
    --------
    dict
        A dictionary with 'success' boolean and 'message' string
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the record exists
        cursor.execute("SELECT id FROM embeddings WHERE material_code = ?", (material_code,))
        record = cursor.fetchone()
        
        if record is None:
            conn.close()
            return {
                'success': False,
                'message': f'No record found with material_code: {material_code}'
            }
        
        # Delete the record
        cursor.execute("DELETE FROM embeddings WHERE material_code = ?", (material_code,))
        conn.commit()
        
        deleted_count = cursor.rowcount
        conn.close()
        
        return {
            'success': True,
            'message': f'Successfully deleted {deleted_count} record(s) with material_code: {material_code}'
        }
        
    except sqlite3.Error as e:
        return {
            'success': False,
            'message': f'Database error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }
