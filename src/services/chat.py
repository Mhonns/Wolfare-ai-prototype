import os
from typing import List, Dict, Any
from openai import OpenAI
import json
import re
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SolarHackerNews:
    def __init__(self):
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY is not set in environment variables")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.upstage.ai/v1/solar"
        )

    def call_api(self, messages: List[Dict[str, str]], model: str = "solar-1-mini-chat") -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages
            )
            response_dict = response.model_dump()
            logger.debug(f"API response: {response_dict}")
            return response_dict
        except Exception as e:
            logger.error(f"Error in API call: {e}")
            return {"error": str(e)}
    #not finished yet
    def summarize_story(self, story: Dict[str, Any]) -> str:
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in summarizing HackerNews stories."},
            {"role": "user", "content": 
            f"""Please analyze the following HackerNews story and structure your summary in JSON format with the following elements:
                {{
                    "title": "The title of the story",
                    "author": "The author of the story",
                    "overview": "A concise overview of the story's main points in 2-3 sentences",
                    "key_topics": [
                        "Topic 1",
                        "Topic 2",
                        "Topic 3"
                    ],
                    "potential_impact": "Brief description of the story's potential impact or significance"
                }}

                Here's the story to analyze:
                {json.dumps(story)}
            """
            }
        ]
        result = self.call_api(messages)
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return ""
    
    def embed_query(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model="solar-embedding-1-large-query",
            input=text
        )
        return response.data[0].embedding

    def embed_document(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model="solar-embedding-1-large-passage",
            input=text
        )
        return response.data[0].embedding
    #not finished yet
    def analyze_user_query(self, query: str) -> Dict[str, Any]:
        logger.debug(f"Analyzing query: {query}")
        messages = [
            {"role": "system", "content": "You are an intelligent AI assistant specialized in analyzing user queries about HackerNews stories."},
            {"role": "user", "content": 
             f"""Analyze the following user query and provide search results:
                1. At least 3 key points to look for in HackerNews stories
                2. Possible related topics or categories
                3. At least 5 exact keywords for searching

                User query: {query}

                Respond in JSON format:
                {{
                    "key_points": ["point1", "point2", "point3"],
                    "related_topics": ["topic1", "topic2"],
                    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
                }}
             """
            }
        ]
        try:
            result = self.call_api(messages)
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    analysis = json.loads(json_str)
                    return analysis
                else:
                    logger.error("No JSON object found in the response")
            else:
                logger.error("Unexpected API response structure")
        except Exception as e:
            logger.error(f"Error in analyze_user_query: {e}")
        
        return {"key_points": [], "related_topics": [], "keywords": []}
    #not finished yet
    def generate_response(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        context = "\n".join([f"Story {i+1}: {json.dumps(result)}" for i, result in enumerate(search_results)])
        
        messages = [
            {"role": "system", "content": "You are an intelligent AI assistant specialized in answering questions about HackerNews stories."},
            {"role": "user", "content": 
             f"""Answer the following query based on the provided HackerNews stories. Focus on extracting and presenting specific information from the stories.
                Include references to the source stories.

                Context: {context}
                User query: {query}

                Respond in JSON format:
                {{
                    "answer": "Your detailed answer here",
                    "references": [
                        {{"story_id": "id", "relevance": "Explanation of relevance"}}
                    ],
                    "confidence": 0.0 
                }}
                // Confidence score between 0-1
             """
            }
        ]
        try:
            result = self.call_api(messages)
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    json_str = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', json_str)
                    response_dict = json.loads(json_str)
                    return response_dict
                else:
                    logger.error("No JSON object found in the response")
            else:
                logger.error("Unexpected API response structure")
        except Exception as e:
            logger.error(f"Error in generate_response: {e}")
        
        return {
            "answer": "Sorry, I couldn't generate a response due to an error.",
            "references": [],
            "confidence": 0.0
        }

    def process_query(self, query: str, vector_db) -> Dict[str, Any]:
        logger.debug(f"Processing query: {query}")
        
        analysis = self.analyze_user_query(query)
        query_embedding = self.embed_query(query)
        
        logger.debug("Performing hybrid search")
        search_results = vector_db.hybrid_search(
            query_embedding=query_embedding,
            keywords=analysis.get('keywords', []),
            n_results=5
        )
        
        logger.debug("Generating response")
        response = self.generate_response(query, search_results)

        final_result = {
            "answer": response.get('answer', "Sorry, I couldn't generate an answer."),
            "references": response.get('references', []),
            "confidence": response.get('confidence', 0.0),
        }
        
        return final_result

# if __name__ == "__main__":
#     solar_hn = SolarHackerNews()
    
#    
#     example_story = {
#         "id": "19121",
#         "title": "Ask HN: Reasonable dev laptop?",
#         "by": "raihansaputra",
#         "text": "So my 2015 Retina MacBook Pro just broke. My fault, my shoddily mounted monitor fell over and hit the laptop, breaking the screen. As I probably won't qualify for the 'Staingate' replacements, footing $600+ for a display replacement is just a bit too much. I'm also looking to move away from Apple products. I'm looking for a reasonable laptop to buy, not looking for the latest specs, just one that can run Ubuntu, have a long battery life (>6 hours preferably), and can handle Modern web browsing (webapps and stuff). Preferably not too heavy to lug around. I'm doing light dev work on Django and trying to learn React/Angular. I'm kinda interested in getting older thinkpads (t430/x230s) but concerned on the battery life part. If any of you have any suggestions, it would be great."
#     }
    
#     # Summarize the story
#     summary = solar_hn.summarize_story(example_story)
#     print("Story summary:", summary)
    
#     # Example query
#     query = "What are some good laptop recommendations for developers?"
    
#     # Process the query (assuming you have a vector_db set up)
#     # result = solar_hn.process_query(query, vector_db)
#     # print("Query result:", result)