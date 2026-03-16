import os
import sys
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from main_window import MainWindow
import func_json
import func_db


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow("main_window.ui")
    window.setWindowIcon(QIcon('icon.ico'))
    window.show()
    
    # ----------------- Create settings.json if not exists ----------------------
    func_json.create_settings_if_not_exists()
    
    # ----------------- Create DB if not exists ------------------------------
    
    db_message = func_db.initialize_database()
    window.statusText.append(db_message)

    # ----------------- Load settings ------------------------------
    default_path = os.path.dirname(os.path.abspath(__file__))
    window.defaultPathLabel.setText(default_path)

    saved_settings = func_json.load_settings()
    use_custom = saved_settings['use_custom_path']
    custom_db_path = saved_settings['custom_db_path']
    num_results = saved_settings['num_results']
    similarity_threshold = saved_settings.get('similarity_threshold', 0.90)

    window.statusText.append(
        f"Loaded settings: use_custom={use_custom}, "
        f"db_path={custom_db_path}, num_results={num_results}, "
        f"similarity_threshold={similarity_threshold}"
    )

    # Apply custom path setting
    if custom_db_path:
        window.customPathLabel.setText(custom_db_path)

    # Check if default path exists
    default_path_exists = os.path.exists(default_path)
    
    # Determine which path to use
    if default_path_exists:
        # Default path exists, use normal logic
        if custom_db_path != "Not set" and use_custom == True:
            window.useCustomCheck.setChecked(True)
            window.activeDirLabel.setText(custom_db_path)
        else:
            window.useCustomCheck.setChecked(False)
            window.activeDirLabel.setText(default_path)
    else:
        # Default path doesn't exist, activate custom path or use root path
        window.statusText.append(f"⚠️ Default path does not exist: {default_path}")
        
        if custom_db_path and custom_db_path != "Not set" and os.path.exists(custom_db_path):
            # Use existing custom path
            window.useCustomCheck.setChecked(True)
            window.activeDirLabel.setText(custom_db_path)
            window.statusText.append(f"✓ Activated custom path: {custom_db_path}")
        else:
            # Use app directory as fallback only if custom path is not set
            app_dir = os.path.dirname(os.path.abspath(__file__))
            window.useCustomCheck.setChecked(True)
            window.activeDirLabel.setText(app_dir)
            window.statusText.append(f"✓ Using app directory as fallback: {app_dir}")
            # Only save app_dir if custom_db_path was not already set
            if not custom_db_path or custom_db_path == "Not set" or custom_db_path == "":
                func_json.save_settings(use_custom_path=True, custom_db_path=app_dir)
            else:
                # Custom path was set but doesn't exist, just enable it
                func_json.save_settings(use_custom_path=True)

    # Apply num results
    if num_results:
        window.numResultsEntry.setText(str(num_results))
    else:
        window.numResultsEntry.setText("12")

    # Apply similarity threshold
    if similarity_threshold:
        window.similarityThresholdEntry.setText(str(similarity_threshold))
    else:
        window.similarityThresholdEntry.setText("0.90")

    # Reload DB path after potential fallback settings update
    func_db.db_path = func_db.get_db_path()
    window.statusText.append(f"Using DB path: {func_db.db_path}")

    # ------------------------------------------------------------------------
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()