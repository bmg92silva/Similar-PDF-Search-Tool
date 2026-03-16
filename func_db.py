import sqlite3
import pandas as pd
import os
import func_json
import hashlib


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
            material_code TEXT NOT NULL UNIQUE,
            embedding BLOB NOT NULL,
            image_blob BLOB NOT NULL,
            file_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Try to add file_hash column if it doesn't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE embeddings ADD COLUMN file_hash TEXT")
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    conn.commit()
    conn.close()


def compute_file_hash(file_path, block_size=65536):
    """
    Compute SHA256 hash of a file
    
    Args:
        file_path: Path to the file
        block_size: Size of blocks to read (default 64KB)
    
    Returns:
        SHA256 hash string
    """
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(block_size), b""):
                sha256_hash.update(block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error computing file hash: {e}")
        return None


def check_duplicate_by_hash_and_similarity(file_hash, embedding_bytes, similarity_threshold=0.90):
    """
    Check if a duplicate exists by file hash and similarity threshold
    
    Args:
        file_hash: SHA256 hash of the file
        embedding_bytes: Embedding bytes of the file
        similarity_threshold: Similarity threshold for duplicate detection
    
    Returns:
        tuple: (is_duplicate, duplicate_info) where duplicate_info is dict with details
    """
    try:
        from func_similar import normalize_query_embedding, calculate_cosine_similarity
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for exact hash match
        cursor.execute(
            'SELECT id, material_code, embedding FROM embeddings WHERE file_hash = ?',
            (file_hash,)
        )
        exact_match = cursor.fetchone()
        
        if exact_match:
            conn.close()
            return (True, {
                'type': 'exact_hash_match',
                'material_code': exact_match[1],
                'similarity': 1.0
            })
        
        # Check for similarity-based duplicates
        cursor.execute('SELECT id, material_code, embedding FROM embeddings')
        all_records = cursor.fetchall()
        conn.close()
        
        if not all_records:
            return (False, None)
        
        query_embedding = normalize_query_embedding(embedding_bytes)
        
        for record_id, material_code, stored_embedding in all_records:
            similarity = calculate_cosine_similarity(query_embedding, stored_embedding)
            
            if similarity >= similarity_threshold:
                return (True, {
                    'type': 'similarity_match',
                    'material_code': material_code,
                    'similarity': similarity
                })
        
        return (False, None)
    
    except Exception as e:
        print(f"Error checking duplicates: {e}")
        return (False, None)


def insert_pdf_row(filename, embedding_bytes, resized_image_bytes, file_hash=None):
    """
    Insert PDF data into database
    
    Args:
        filename: Original filename
        embedding_bytes: Pre-generated embedding bytes
        resized_image_bytes: Pre-processed resized image bytes
        file_hash: SHA256 hash of the file (optional)
    
    Returns:
        Row ID of inserted record
    """
    # Insert into database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO embeddings (material_code, embedding, image_blob, file_hash)
        VALUES (?, ?, ?, ?)
    """, (filename, embedding_bytes, resized_image_bytes, file_hash))
    
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
