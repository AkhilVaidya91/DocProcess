import os
import streamlit as st
from pathlib import Path
from PyPDF2 import PdfReader
import sqlite3
import openai
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document as LlamaDocument
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import SimpleVectorStore
from datetime import datetime

openai.api_key = os.getenv("OPENAI_API_KEY")

class Document:
    def __init__(self):
        # Create necessary directories if they don't exist
        self.uploads_dir = Path("uploads")
        self.embeddings_dir = Path("embeddings")
        self.uploads_dir.mkdir(exist_ok=True)
        self.embeddings_dir.mkdir(exist_ok=True)
        
        # Initialize database
        self.init_database()

    def validateDocument(self, uploaded_file):
        """
        Validate the uploaded document's size and type
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            tuple: (bool, str) - (is_valid, error_message)
        """
        # Check file type
        if uploaded_file.type != "application/pdf":
            return False, "Invalid Document Type"
        
        # Check file size (1MB = 1048576 bytes)
        if uploaded_file.size > 1048576:
            return False, "Invalid Document Size"
        
        return True, ""
    
    def init_database(self):
        """Initialize SQLite database with required table"""
        conn = sqlite3.connect('documents.db')
        cursor = conn.cursor()
        
        # Create users_documents table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def upload(self, uploaded_file, user_id):
        """
        Upload the document to the uploads folder and store metadata in database
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            user_id: String identifier for the user
            
        Returns:
            bool: Success status of upload
        """
        try:
            if uploaded_file is None:
                return False
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{uploaded_file.name}"
            file_path = self.uploads_dir / filename
            
            # Save file to uploads directory
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Store file information in database
            conn = sqlite3.connect('documents.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users_documents (user_id, filename) VALUES (?, ?)",
                (user_id, filename)
            )
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"Error in upload: {str(e)}")
            return False

    def processDocument(self, filename):
        """
        Extract text from PDF document
        
        Args:
            filename: Name of the file to process
            
        Returns:
            str: Extracted text from the PDF
        """
        try:
            file_path = self.uploads_dir / filename
            
            if not file_path.exists():
                raise FileNotFoundError(f"File {filename} not found in uploads directory")
            
            # Extract text from PDF
            pdf_reader = PdfReader(str(file_path))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            return text
            
        except Exception as e:
            st.error(f"Error in processing document: {str(e)}")
            return None

    def storeEmbeddings(self, text, filename):
        """
        Create and store embeddings using LlamaIndex
        
        Args:
            text: Extracted text from the document
            filename: Name of the file to use for storing embeddings
            
        Returns:
            bool: Success status of embedding storage
        """
        try:
            # Remove file extension from filename
            base_filename = Path(filename).stem
            
            # Create a LlamaIndex document
            documents = [LlamaDocument(text=text)]
            
            # Create vector store and index
            vector_store = SimpleVectorStore()
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context
            )
            
            # Save the index
            index.storage_context.persist(persist_dir=str(self.embeddings_dir / base_filename))
            
            return True
            
        except Exception as e:
            st.error(f"Error in storing embeddings: {str(e)}")
            return False

# Example Streamlit interface
def main():
    st.title("Document Upload and Processing")
    
    # Initialize Document class
    doc_processor = Document()
    
    # Simple user ID input (in a real app, this would be handled by authentication)
    user_id = st.text_input("Enter User ID")
    
    # File upload widget
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None and user_id:
        if st.button("Process Document"):
            # Upload file

            is_valid, error_message = doc_processor.validateDocument(uploaded_file)
            if not is_valid:
                st.error(error_message)
            else:
                if doc_processor.upload(uploaded_file, user_id):
                    st.success("File uploaded successfully!")
                    
                    # Process document
                    text = doc_processor.processDocument(uploaded_file.name)
                    if text:
                        st.success("Document processed successfully!")
                        
                        # Store embeddings
                        if doc_processor.storeEmbeddings(text, uploaded_file.name):
                            st.success("Embeddings stored successfully!")
                        else:
                            st.error("Error storing embeddings")
                    else:
                        st.error("Error processing document")
                else:
                    st.error("Error uploading file")

if __name__ == "__main__":
    main()