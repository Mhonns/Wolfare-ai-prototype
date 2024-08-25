import os
import json
import random
import uuid
import chromadb
from typing import Dict, Any, List
from services.chat import SolarHackerNews
import pypdf
from langchain.text_splitter import RecursiveCharacterTextSplitter


class VectorDB:
    def __init__(self):
        persist_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'chroma_db')
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.chroma_client.get_or_create_collection(name="hacker_news_stories")
        self.solar = SolarHackerNews() # Initialize Solar LLM
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    @staticmethod
    def clean_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean metadata by removing None values and ensuring all values are of supported types.
        """
        cleaned = {}
        for key, value in metadata.items():
            if value is not None:
                if isinstance(value, (str, int, float, bool)):
                    cleaned[key] = value
                else:
                    cleaned[key] = str(value)  # Convert other types to string
        return cleaned
    

    #Json format
    def save_to_vector_db(self, data: Dict[str, Any]) -> str:
        story_id = str(data['id'])  # Ensure ID is a string
        metadata = self.clean_metadata(data['metadata'])
        text = metadata.pop('text', '')  # Remove 'text' from metadata and store it separately
        
        # Generate embedding using Solar LLM
        embedding = self.solar.embed_document(text)
        
        self.collection.add(
            ids=[story_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[text]
        )
        
        return story_id
    #Multiple ids of Json
    def save_multiple_to_vector_db(self, data_list: List[Dict[str, Any]]) -> List[str]:
        ids = []
        embeddings = []
        metadatas = []
        documents = []

        for data in data_list:
            story_id = str(data['id'])  # Ensure ID is a string
            metadata = self.clean_metadata(data['metadata'])
            text = metadata.pop('text', '')  # Remove 'text' from metadata and store it separately
            
            # Generate embedding using Solar LLM
            embedding = self.solar.embed_document(text)
            
            ids.append(story_id)
            embeddings.append(embedding)
            metadatas.append(metadata)
            documents.append(text)

        # Save in batches to handle large datasets
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_embeddings = embeddings[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            batch_documents = documents[i:i+batch_size]
            
            self.collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
                documents=batch_documents
            )
        
        return ids
    
    #pdf file processing
    def process_pdf(self, pdf_path: str) -> List[str]:
        """Process a PDF file and return a list of text chunks."""
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        return self.text_splitter.split_text(text)
    

    #save pdf into vector db
    def save_pdf_to_vector_db(self, pdf_path: str) -> List[str]:
        """Process a PDF and save its chunks to Chroma DB."""
        chunks = self.process_pdf(pdf_path)
        ids = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{os.path.basename(pdf_path)}_{i}"
            metadata = {
                "source": pdf_path,
                "chunk": i,
                "type": "pdf"
            }
            embedding = self.solar.embed_document(chunk)
            
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[self.clean_metadata(metadata)],
                documents=[chunk]
            )
            ids.append(chunk_id)
        
        return ids

    #save multiple_pdfs to vector_db
    def save_multiple_pdfs_to_vector_db(self, pdf_paths: List[str]) -> List[str]:
        """Process multiple PDFs and save their chunks to Chroma DB."""
        all_ids = []
        for pdf_path in pdf_paths:
            ids = self.save_pdf_to_vector_db(pdf_path)
            all_ids.extend(ids)
        return all_ids

    def query_vector_db(self, query_text: str, n_results: int = 5, filter_condition: Dict[str, Any] = None) -> Dict[str, Any]:
        query_embedding = self.solar.embed_query(query_text)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_condition,
            include=["documents", "metadatas", "distances"]
        )
        return results
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the current state of the database."""
        total_items = self.collection.count()
        sample_ids = self.collection.get(limit=5)['ids']
        return {
            "total_items": total_items,
            "sample_ids": sample_ids
        }
    def verify_data_storage(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify that data from data.json has been correctly stored in Chroma DB."""
        verification_results = {
            "success": True,
            "message": "All data verified successfully",
            "total_stories": len(data_list),
            "verified_stories": 0,
            "mismatches": []
        }

        for data in data_list:
            story_id = str(data['id'])  # Ensure ID is a string
            original_metadata = self.clean_metadata(data['metadata'].copy())
            original_text = original_metadata.pop('text', '')

            # Fetch the stored data
            try:
                stored_data = self.collection.get(
                    ids=[story_id],
                    include=['documents', 'metadatas']
                )

                if not stored_data['ids']:
                    verification_results["mismatches"].append({
                        "id": story_id,
                        "error": "Story not found in database"
                    })
                    continue

                stored_metadata = stored_data['metadatas'][0]
                stored_text = stored_data['documents'][0]

                # Compare metadata
                if original_metadata != stored_metadata:
                    verification_results["mismatches"].append({
                        "id": story_id,
                        "error": "Metadata mismatch",
                        "original": original_metadata,
                        "stored": stored_metadata
                    })

                # Compare text
                if original_text != stored_text:
                    verification_results["mismatches"].append({
                        "id": story_id,
                        "error": "Text mismatch",
                        "original_preview": original_text[:100],
                        "stored_preview": stored_text[:100]
                    })

                verification_results["verified_stories"] += 1

            except Exception as e:
                verification_results["mismatches"].append({
                    "id": story_id,
                    "error": f"Error during verification: {str(e)}"
                })

        if verification_results["mismatches"]:
            verification_results["success"] = False
            verification_results["message"] = f"Verification completed with {len(verification_results['mismatches'])} mismatches"

        return verification_results


    @staticmethod
    def load_json_data(file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, 'r') as file:
            return json.load(file)
        
    @staticmethod
    def sample_json_data(data: List[Dict[str, Any]], sample_size: int) -> List[Dict[str, Any]]:
        """
        Sample a subset of the JSON data.
        
        :param data: The full list of data items
        :param sample_size: The number of items to sample
        :return: A list containing the sampled items
        """
        return random.sample(data, min(sample_size, len(data)))


# # Create an instance of VectorDB
vector_db = VectorDB()