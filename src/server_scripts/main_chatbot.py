#from src.pages import wolfare_controller
from utils.config import load_environment_variables
from database.vector_db import vector_db
from services.chat import solar_hn
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main(prompt: str):
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

    # # Save a single PDF
    # pdf_path = "GlobalThreatReport2024.pdf"
    # saved_ids = vector_db.save_pdf_to_vector_db(pdf_path)
    # print(f"Saved {len(saved_ids)} chunks from {pdf_path} to Chroma DB")


    # while True:
    #     query = input("\nEnter your question: ").strip()
        
    #     if query.lower() == 'exit':
    #         print("Thank you for using our Cyber Security News Chatbot")
    #         break

    # try:
    #     result = solar_hn.process_query(query, vector_db)
        
    #     print("\nAnswer:", result["answer"])
        
    #     if result["references"]:
    #         print("\nReferences:")
    #         for ref in result["references"]:
    #             print(f"- Story ID: {ref['story_id']}, Relevance: {ref['relevance']}")
        
    #     print(f"\nConfidence: {result['confidence']:.2f}")
    
    # except Exception as e:
    #     logger.error(f"Error processing query: {e}")
    #     print("Sorry, an error occurred while processing your query. Please try again.")
    e = ""
    query = prompt.strip()

    try:
        result = solar_hn.process_query(query, vector_db)
        
        print("\nAnswer:", result["answer"])
        
        if result["references"]:
            print("\nReferences:")
            for ref in result["references"]:
                print(f"- Story ID: {ref['story_id']}, Relevance: {ref['relevance']}")
        
        print(f"\nConfidence: {result['confidence']:.2f}")
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        print("Sorry, an error occurred while processing your query. Please try again.")

    return f'{e}', result["answer"], f"\nConfidence: {result['confidence']:.2f}"

# if __name__ == "__main__":
#     main()