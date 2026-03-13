import os
import json

def create_settings_if_not_exists(json_filepath='settings.json'):
    """
    Create settings.json file with default values if it doesn't exist
    
    Args:
        json_filepath: Path to settings JSON file
    
    Returns:
        Dictionary with settings
    """
    default_settings = {
        "use_custom_path": False,
        "custom_db_path": "",
        "num_results": 10
    }
    
    if not os.path.exists(json_filepath):
        try:
            with open(json_filepath, 'w') as f:
                json.dump(default_settings, f, indent=4)
            print(f"Settings file created: {json_filepath}")
        except Exception as e:
            print(f"Error creating settings file: {e}")
    
    return default_settings


def load_settings(json_filepath='settings.json'):
    """
    Load settings from JSON file if it exists
    
    Args:
        settings_path: Path to settings JSON file
    
    Returns:
        Dictionary with settings or default values
    """
    default_settings = {
        "use_custom_path": False,
        "custom_db_path": "",
        "num_results": 10
    }
    
    if os.path.exists(json_filepath):
        try:
            with open(json_filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return default_settings
    else:
        return default_settings


import json

def save_settings( use_custom_path=None, custom_db_path=None, num_results=None, json_filepath='settings.json'):
    """
    Modify settings.json file with provided parameters.
    Only updates fields that are not None/empty.
    
    Parameters:
    - json_filepath: str - Path to the settings.json file
    - use_custom_path: bool or None - Whether to use custom path
    - custom_db_path: str or None - Custom database path
    - num_results: int or None - Number of results
    """
    # Read the existing JSON file
    with open(json_filepath, 'r') as f:
        config = json.load(f)
    
    # Only update if the value is not None
    if use_custom_path is not None:
        config["use_custom_path"] = use_custom_path
    
    # For strings, also check if not empty
    if custom_db_path is not None and custom_db_path != "":
        config["custom_db_path"] = custom_db_path
    
    if num_results is not None:
        config["num_results"] = num_results
    
    # Write back to the file
    with open(json_filepath, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"Settings updated successfully in {json_filepath}")
    return config
