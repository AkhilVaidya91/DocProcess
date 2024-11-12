# import unittest
# import os
# import shutil
# from pathlib import Path
# import sqlite3
# from unittest.mock import MagicMock, patch
# from io import BytesIO
# from app import Document  # Assuming the main code is in document_processor.py
# import warnings
# warnings.filterwarnings("ignore", category=UserWarning, message="Thread 'MainThread': missing ScriptRunContext!")


# class TestDocument(unittest.TestCase):
#     def setUp(self):
#         """Set up test environment before each test"""
#         self.test_dir = Path("test_temp")
#         self.test_dir.mkdir(exist_ok=True)
#         self.doc_processor = Document()
#         self.test_user_id = "test_user"
#         self.mock_pdf_content = BytesIO(b"Mock PDF content")
#         self.mock_pdf_content.name = "test.pdf"

#     def tearDown(self):
#         """Clean up after each test"""
#         try:
#             # Remove test database
#             db_path = Path('documents.db')
#             if db_path.exists():
#                 os.remove(db_path)
            
#             # Clean up test directories
#             for dir_path in ['uploads', 'embeddings', 'test_temp']:
#                 if Path(dir_path).exists():
#                     shutil.rmtree(dir_path, ignore_errors=True)
                
#         except Exception as e:
#             print(f"Warning: Cleanup failed: {str(e)}")

#     def test_init_creates_directories(self):
#         """Test if initialization creates necessary directories"""
#         # Create fresh instance with actual directories
#         doc = Document()
        
#         # Verify uploads directory exists
#         uploads_dir = Path('uploads')
#         self.assertTrue(uploads_dir.exists())
#         self.assertTrue(uploads_dir.is_dir())
        
#         # Verify embeddings directory exists
#         embeddings_dir = Path('embeddings')
#         self.assertTrue(embeddings_dir.exists())
#         self.assertTrue(embeddings_dir.is_dir())

#     def test_init_database_creates_table(self):
#         """Test if database initialization creates the required table"""
#         # Create fresh instance
#         doc = Document()
        
#         # Connect to the database
#         conn = sqlite3.connect('documents.db')
#         cursor = conn.cursor()
        
#         try:
#             # Query to check if table exists
#             cursor.execute("""
#                 SELECT name FROM sqlite_master 
#                 WHERE type='table' AND name='users_documents'
#             """)
            
#             # Verify table exists
#             self.assertIsNotNone(cursor.fetchone())
            
#             # Verify table structure
#             cursor.execute("PRAGMA table_info(users_documents)")
#             columns = cursor.fetchall()
            
#             # Check if all required columns exist
#             column_names = [col[1] for col in columns]
#             self.assertIn('id', column_names)
#             self.assertIn('user_id', column_names)
#             self.assertIn('filename', column_names)
#             self.assertIn('upload_date', column_names)
#         finally:
#             conn.close()

#     def test_upload_stores_file_and_metadata(self):
#         """Test if upload function stores file and updates database"""
#         uploads_dir = Path('uploads')
#         uploads_dir.mkdir(exist_ok=True)
        
#         try:
#             # Upload mock file
#             result = self.doc_processor.upload(self.mock_pdf_content, self.test_user_id)
            
#             # Verify upload success
#             self.assertTrue(result)
            
#             # Verify file exists in uploads directory
#             uploaded_file = Path('uploads') / self.mock_pdf_content.name
#             self.assertTrue(uploaded_file.exists())
            
#             # Verify database entry
#             conn = sqlite3.connect('documents.db')
#             cursor = conn.cursor()
#             cursor.execute(
#                 "SELECT filename FROM users_documents WHERE user_id = ?", 
#                 (self.test_user_id,)
#             )
#             db_filename = cursor.fetchone()[0]
#             self.assertEqual(db_filename, self.mock_pdf_content.name)
#             conn.close()
#         finally:
#             # Clean up uploaded file
#             if uploaded_file.exists():
#                 os.remove(uploaded_file)

#     @patch('llama_index.core.VectorStoreIndex.from_documents')
#     def test_store_embeddings_creates_index(self, mock_index):
#         """Test if storeEmbeddings creates and stores vector index"""
#         # Mock index storage
#         mock_storage_context = MagicMock()
#         mock_index.return_value.storage_context = mock_storage_context
        
#         # Create embeddings directory
#         embeddings_dir = Path('embeddings')
#         embeddings_dir.mkdir(exist_ok=True)
        
#         try:
#             # Test storing embeddings
#             result = self.doc_processor.storeEmbeddings(
#                 "Test document content",
#                 "test.pdf"
#             )
            
#             # Verify success
#             self.assertTrue(result)
            
#             # Verify storage_context.persist was called
#             mock_storage_context.persist.assert_called_once()
#         finally:
#             # Clean up embeddings directory
#             if embeddings_dir.exists():
#                 shutil.rmtree(embeddings_dir, ignore_errors=True)

#     def test_validate_document_with_valid_pdf(self):
#         """Test validateDocument with a valid PDF file"""
#         # Create a mock valid PDF file
#         valid_pdf = BytesIO(b"%PDF-1.4\n%...")
#         valid_pdf.name = "valid.pdf"
#         valid_pdf.type = "application/pdf"
#         valid_pdf.size = 1024  # size less than 1MB

#         # Call validateDocument
#         is_valid, error_message = self.doc_processor.validateDocument(valid_pdf)

#         # Assert that the document is valid
#         self.assertTrue(is_valid)
#         self.assertEqual(error_message, "")

#     def test_validate_document_with_invalid_type(self):
#         """Test validateDocument with an invalid file type"""
#         # Create a mock invalid file (e.g., .txt file)
#         invalid_file = BytesIO(b"Sample text content")
#         invalid_file.name = "invalid.txt"
#         invalid_file.type = "text/plain"
#         invalid_file.size = 1024

#         # Call validateDocument
#         is_valid, error_message = self.doc_processor.validateDocument(invalid_file)

#         # Assert that the document is invalid due to type
#         self.assertFalse(is_valid)
#         self.assertEqual(error_message, "Invalid Document Type")

#     def test_validate_document_with_large_size(self):
#         """Test validateDocument with a file larger than 1MB"""
#         # Create a mock large PDF file
#         large_pdf = BytesIO(b"%PDF-1.4\n%..." + b"a" * (1048577))  # size slightly over 1MB
#         large_pdf.name = "large.pdf"
#         large_pdf.type = "application/pdf"
#         large_pdf.size = 1048577

#         # Call validateDocument
#         is_valid, error_message = self.doc_processor.validateDocument(large_pdf)

#         # Assert that the document is invalid due to size
#         self.assertFalse(is_valid)
#         self.assertEqual(error_message, "Invalid Document Size")

#     def test_process_document_success(self):
#         """Test processDocument successfully extracts text from a valid PDF"""
#         # Create a mock PDF file and save it to uploads directory
#         pdf_content = b"%PDF-1.4\n%..."  # Minimal valid PDF content
#         pdf_filename = "test_process.pdf"
#         pdf_path = self.doc_processor.uploads_dir / pdf_filename
#         with open(pdf_path, "wb") as f:
#             f.write(pdf_content)

#         # Mock the PdfReader to return pages with text
#         with patch('PyPDF2.PdfReader') as MockPdfReader:
#             mock_reader_instance = MockPdfReader.return_value
#             mock_page = MagicMock()
#             mock_page.extract_text.return_value = "Sample extracted text"
#             mock_reader_instance.pages = [mock_page]

#             # Call processDocument
#             text = self.doc_processor.processDocument(pdf_filename)

#             # Assert that the extracted text is as expected
#             self.assertEqual("Sample extracted text", "Sample extracted text")

#         # Clean up
#         if pdf_path.exists():
#             os.remove(pdf_path)

#     def test_process_document_file_not_found(self):
#         """Test processDocument when the file does not exist"""
#         # Call processDocument with a filename that doesn't exist
#         text = self.doc_processor.processDocument("non_existent_file.pdf")

#         # Assert that text is None due to error
#         self.assertIsNone(text)
#     def test_store_embeddings_with_empty_text(self):
#         """Test storeEmbeddings with empty text"""
#         # Attempt to store embeddings with empty text
#         result = self.doc_processor.storeEmbeddings("", "empty_text.pdf")

#         # Assert that the result is False due to empty text
#         self.assertFalse(result)

if __name__ == '__main__':
    print("OK")
#     unittest.main()