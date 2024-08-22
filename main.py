#from src.pages import wolfare_controller
from src.utils.config import load_environment_variables
from src.database.vector_db import vector_db
#import os
def main():
    #vector_db = VectorDB()

    # Load environment variables
    load_environment_variables()
    # Load data from JSON file
    data = vector_db.load_json_data('data/data.json')
    
    # Save all stories to Chroma DB
    saved_ids = vector_db.save_multiple_to_vector_db(data)
    print(f"Saved {len(saved_ids)} stories to Chroma DB")
    
    # Example query
    query_results = vector_db.query_vector_db("dev laptop recommendations")
    print("Query results:", query_results)


if __name__ == "__main__":
    main()