import os
import json
import uuid
import chromadb
from typing import Dict, Any, List
from services.chat import SolarHackerNews

'''
   {
        "id": "19123",
        "vector": [],
        "metadata": {
            "article_id": "19123",
            "title": "Ask HN: Should new grad go to startup or big company?",
            "source": "",
            "time": 1540081436,
            "by": "ziyun",
            "type": "story",
            "text": "I will be graduating next semester. This would be the job hunting season. Just wondering if any of you have suggestions. Should I head into the startups or big company? Thanks!",
            "chunk_index": null
        }
    },
'''

class VectorDB:
    def __init__(self):
        persist_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'chroma_db')
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.chroma_client.get_or_create_collection(name="hacker_news_stories")
        self.solar = SolarHackerNews() # Initialize Solar LLM

    def save_to_vector_db(self, data: Dict[str, Any]) -> str:
        story_id = data['id']
        metadata = data['metadata']
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

    def save_multiple_to_vector_db(self, data_list: List[Dict[str, Any]]) -> List[str]:
        ids = []
        embeddings = []
        metadatas = []
        documents = []

        for data in data_list:
            story_id = data['id']
            metadata = data['metadata']
            text = metadata.pop('text', '')  # Remove 'text' from metadata and store it separately
            
            # Generate embedding using Solar LLM
            embedding = self.solar.embed_document(text)
            
            ids.append(story_id)
            embeddings.append(embedding)
            metadatas.append(metadata)
            documents.append(text)

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        
        return ids

    def query_vector_db(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        query_embedding = self.solar.embed_query(query_text)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        return results

    @staticmethod
    def load_json_data(file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, 'r') as file:
            return json.load(file)

# Usage example:
# if __name__ == "__main__":
#     vector_db = VectorDB()
    
#     # Load data from JSON file
#     data = vector_db.load_json_data('data/data.json')
    
#     # Save all stories to Chroma DB
#     saved_ids = vector_db.save_multiple_to_vector_db(data)
#     print(f"Saved {len(saved_ids)} stories to Chroma DB")
    
#     # Example query
#     query_results = vector_db.query_vector_db("dev laptop recommendations")
#     print("Query results:", query_results)


# # Create an instance of VectorDB
vector_db = VectorDB()