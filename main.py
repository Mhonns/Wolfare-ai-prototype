#from src.pages import wolfare_controller
from src.utils.config import load_environment_variables
from src.database.vector_db import vector_db
#import os
def main():
    #vector_db = VectorDB()

    # Load environment variables
    load_environment_variables()
    
    # Load data from JSON file
    # data = vector_db.load_json_data('data/data.json')
    # # Save all stories to Chroma DB
    # #saved_ids = vector_db.save_multiple_to_vector_db(data)
    # #print(f"Saved {len(saved_ids)} stories to Chroma DB")  
    # # Sample the data
    # sample_size = 10  # Adjust this value as needed
    # sampled_data = vector_db.sample_json_data(data, sample_size)
    # print(f"Working with a sample of {len(sampled_data)} items")
    # saved_ids = vector_db.save_multiple_to_vector_db(sampled_data)
    # print(f"Saved {len(saved_ids)} stories to Chroma DB")

    # Save a single PDF
    pdf_path = "GlobalThreatReport2024.pdf"
    saved_ids = vector_db.save_pdf_to_vector_db(pdf_path)
    print(f"Saved {len(saved_ids)} chunks from {pdf_path} to Chroma DB")


    query = "how to privilege escalation in linux" 
    results = vector_db.query_vector_db(query, n_results=3, filter_condition={"type": "pdf"})
    for i, (doc, metadata, distance) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0]), 1):
        print(f"\nResult {i}:")
        print(f"Distance: {distance}")
        print(f"Source: {metadata['source']}")
        print(f"Chunk: {metadata['chunk']}")
        print(f"Text preview: {doc[:300]}...")


if __name__ == "__main__":
    main()