import os
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QApplication

import func_pdf
import func_db
import func_similar
import func_json
import func_ui


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, ui_path: str = "main_window.ui"):
        super().__init__()

        # Load the UI designed in Qt Designer
        uic.loadUi(ui_path, self)

        # --- Tab 1: Similar Search widgets ---
        # Upload PDFs group
        self.selectPdfsBtn = self.findChild(QtWidgets.QPushButton, "selectPdfsBtn")
        self.processBtn = self.findChild(QtWidgets.QPushButton, "processBtn")
        self.uploadProgressBar = self.findChild(QtWidgets.QProgressBar, "uploadProgressBar")
        self.progressLabel = self.findChild(QtWidgets.QLabel, "progressLabel")

        # Search by Material Code group
        self.materialEntry = self.findChild(QtWidgets.QLineEdit, "materialEntry")

        # Search Similar PDFs (File) group
        self.selectQueryBtn = self.findChild(QtWidgets.QPushButton, "selectQueryBtn")
        self.findSimilarBtn = self.findChild(QtWidgets.QPushButton, "findSimilarBtn")

        # Console Output group
        self.consoleText = self.findChild(QtWidgets.QTextEdit, "consoleText")

        # Results scroll area
        self.resultsScrollArea = self.findChild(QtWidgets.QScrollArea, "resultsScrollArea")
        self.resultsWidget = self.findChild(QtWidgets.QWidget, "resultsWidget")

        # Tab widget (for switching tabs programmatically if needed)
        self.tabWidget = self.findChild(QtWidgets.QTabWidget, "tabWidget")

        # --- Tab 2: Settings widgets ---
        # Directory group
        self.defaultPathLabel = self.findChild(QtWidgets.QLabel, "defaultPathLabel")
        self.customPathLabel = self.findChild(QtWidgets.QLabel, "customPathLabel")
        self.activeDirLabel = self.findChild(QtWidgets.QLabel, "activeDirLabel")
        self.useCustomCheck = self.findChild(QtWidgets.QCheckBox, "useCustomCheck")
        self.browseCustomBtn = self.findChild(QtWidgets.QPushButton, "browseCustomBtn")
        self.applyDirBtn = self.findChild(QtWidgets.QPushButton, "applyDirBtn")

        # Search configuration group
        self.numResultsEntry = self.findChild(QtWidgets.QLineEdit, "numResultsEntry")
        self.similarityThresholdEntry = self.findChild(QtWidgets.QLineEdit, "similarityThresholdEntry")
        self.saveNumResultsBtn = self.findChild(QtWidgets.QPushButton, "saveNumResultsBtn")

        # Status group
        self.statusText = self.findChild(QtWidgets.QTextEdit, "statusText")

        # status bar
        self.statusbar = self.findChild(QtWidgets.QStatusBar, "statusbar")

        # Upload PDFs
        self.selectPdfsBtn.clicked.connect(self.on_select_pdfs_clicked)
        self.processBtn.clicked.connect(self.on_process_pdfs_clicked)


        # File-based similar search
        self.selectQueryBtn.clicked.connect(self.on_select_query_clicked)
        self.findSimilarBtn.clicked.connect(self.on_find_similar_clicked)

        # Settings: directories
        self.browseCustomBtn.clicked.connect(self.on_browse_custom_clicked)
        self.applyDirBtn.clicked.connect(self.on_apply_dir_clicked)

        # Settings: search configuration
        self.saveNumResultsBtn.clicked.connect(self.on_save_num_results_clicked)

    # -------- Event Handler Methods --------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    
    selected_pdfs = []
    number_of_pdfs = 0
    single_pdf = ""
    
    def on_select_pdfs_clicked(self):
        db_dir = self.activeDirLabel.text()
        """Handle PDF file selection"""
        # Open file dialog to select multiple PDF files
        files, _ = QFileDialog.getOpenFileNames(self,"Select PDF Files","","PDF Files (*.pdf);;All Files (*.*)")
        
        if files:
            self.selected_pdfs = files
            self.number_of_pdfs = len(files)
            self.progressLabel.setText(f"{self.number_of_pdfs} PDF file(s) selected")
        else:
            self.selected_pdfs = []
            self.number_of_pdfs = 0

    def on_process_pdfs_clicked(self):
        """Process selected PDF files and convert to images"""
        if not self.selected_pdfs:
            QMessageBox.warning(self,"No Files Selected","Please select PDF files first")
            return
        
        processed_count = 0
        failed_files = []
        
        # Load similarity threshold setting
        saved_settings = func_json.load_settings()
        similarity_threshold = saved_settings.get('similarity_threshold', 0.90)
        
        # Initialize progress bar
        total_files = len(self.selected_pdfs)
        self.uploadProgressBar.setRange(0, total_files)
        self.uploadProgressBar.setValue(0)
        
        # Process the pdf file
        for index, pdf_path in enumerate(self.selected_pdfs):
            try:
                # Convert first page of PDF to image
                image_bytes, filename = func_pdf.pdf_to_image(pdf_path, page_num=0)
                
                # Compute file hash
                file_hash = func_db.compute_file_hash(pdf_path)
                self.consoleText.append(f"Processing: {filename}")
                
                # Check if material code exists
                if func_db.material_code_exists(filename):
                    self.consoleText.append(f"⚠️ Material code already exists: {filename}")
                else:
                    # Generate embedding
                    try:
                        embedding_bytes, image_bytes = func_pdf.embedding_pipeline(image_bytes)
                        self.consoleText.append("✓ Embedding generated.")
                    except Exception as e:
                        self.consoleText.append(f"✗ Error generating embedding: {e}")
                        raise
                    
                    # Check for duplicates by hash and similarity
                    is_duplicate, duplicate_info = func_db.check_duplicate_by_hash_and_similarity(
                        file_hash, embedding_bytes, similarity_threshold
                    )
                    
                    if is_duplicate:
                        self.consoleText.append(
                            f"⚠️ Potential duplicate found!\n"
                            f"   Type: {duplicate_info['type']}\n"
                            f"   Duplicate of: {duplicate_info['material_code']}\n"
                            f"   Similarity: {duplicate_info['similarity']:.4f}"
                        )
                    
                    # Add PDF to DB
                    try:
                        row_id = func_db.insert_pdf_row(filename, embedding_bytes, image_bytes, file_hash)
                        self.consoleText.append(f"✓ PDF inserted into database: row ID {row_id}")
                    except Exception as e:
                        self.consoleText.append(f"✗ Error inserting PDF into database: {e}")
                        raise
                
                processed_count += 1
                
                # Update progress bar
                self.uploadProgressBar.setValue(index + 1)
                self.progressLabel.setText(f"{index + 1} of {self.number_of_pdfs} PDFs Processed")
                
                QApplication.processEvents()
                
            except Exception as e:
                failed_files.append(f"{filename}: {str(e)}")
                continue
        
        # Reset progress bar when done
        self.uploadProgressBar.setValue(total_files)
        
        # Show results
        if failed_files:
            QMessageBox.warning(
                self,
                "Processing Complete with Errors",
                f"Processed: {processed_count}/{self.number_of_pdfs}\n\n"
                f"Failed files:\n" + "\n".join(failed_files)
            )
        else:
            QMessageBox.information(
                self,
                "Success",
                f"Successfully processed all {processed_count} PDF file(s)"
            )


    def on_select_query_clicked(self):
        # Open file dialog to select a single PDF file
        self.single_pdf, _ = QFileDialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf);;All Files (*.*)")

        if self.single_pdf:
            self.selected_pdfs = [self.single_pdf]  # Store as single-item list for compatibility
        pass

    def on_find_similar_clicked(self):
        # Check if a PDF has been selected
        if self.single_pdf is None or not self.single_pdf:
            self.consoleText.append("Error: No PDF selected. Please select a PDF first.")
            return
        
        image_bytes, filename = func_pdf.pdf_to_image(self.single_pdf)
        self.consoleText.append(f"Searching for PDFs similar to: {filename}")
        self.consoleText.append("Converting PDF to image...")
        
        # Generate embedding
        try:
            embedding_bytes, image_bytes = func_pdf.embedding_pipeline(image_bytes)
            self.consoleText.append("✓ Embedding generated.")
        except Exception as e:
            self.consoleText.append(f"✗ Error generating embedding: {e}")
            return
        
        # Load settings for number of results
        saved_settings = func_json.load_settings()
        num_results = saved_settings.get('num_results', 12)
        
        # Get similar embeddings with images
        results = func_similar.find_similar_pipeline(embedding_bytes, top_k=num_results)
        
        # Print results to console
        if results:
            self.consoleText.append(f"\n✓ Found {len(results)} similar PDFs:\n")
            for idx, (material_code, similarity, _) in enumerate(results, 1):
                self.consoleText.append(f"{idx}. {material_code}\n   Similarity: {similarity:.4f}\n")
            self.consoleText.append("")
        else:
            self.consoleText.append("⚠️ No similar PDFs found in database.")
        
        # Display results in grid
        func_ui.populate_results_scroll_area(self.resultsScrollArea, results)

    def on_browse_custom_clicked(self):
        directory_path = QFileDialog.getExistingDirectory(self, "Select Directory", "")
        if directory_path:
            self.customPathLabel.setText(directory_path)
        else:
            self.customPathLabel.setText("Not set")

    def on_apply_dir_clicked(self):
        use_custom_check = self.useCustomCheck.isChecked()
        default_path = self.defaultPathLabel.text()
        custom_path = self.customPathLabel.text()

        # Determine which path to save
        if use_custom_check and custom_path != "Not set" and custom_path != "":
            func_json.save_settings(use_custom_path=use_custom_check, custom_db_path=custom_path)
            self.activeDirLabel.setText(custom_path)
        else:
            func_json.save_settings(use_custom_path=use_custom_check)
            self.activeDirLabel.setText(default_path)
        
        QMessageBox.information(self, "Apply Directory", "Settings applied successfully!")

    def on_save_num_results_clicked(self):
        text = self.numResultsEntry.text().strip()
        threshold_text = self.similarityThresholdEntry.text().strip()

        if text == "":
            QMessageBox.warning(self, "Error", "Please enter a valid number of results")
            return

        if threshold_text == "":
            QMessageBox.warning(self, "Error", "Please enter a valid similarity threshold")
            return

        try:
            num_results = int(text)
            if num_results <= 0:
                QMessageBox.warning(self, "Error", "Please enter a positive number for results")
                return
            
            similarity_threshold = float(threshold_text)
            if similarity_threshold < 0 or similarity_threshold > 1:
                QMessageBox.warning(self, "Error", "Similarity threshold must be between 0 and 1")
                return

            func_json.save_settings(num_results=num_results, similarity_threshold=similarity_threshold)
            QMessageBox.information(self, "Save Settings", 
                                  f"Settings saved:\nNumber of results: {num_results}\nSimilarity threshold: {similarity_threshold}")
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter valid numbers")
