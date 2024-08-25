import os
from typing import List, Dict, Any
from openai import OpenAI
import json
import re
import logging
from langgraph.graph import Graph, END
#from langgraph.prebuilt import ToolExecutor

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

        self.graph = self.create_rag_graph()

    def call_api(self, messages: List[Dict[str, str]], model: str = "solar-1-mini-chat") -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages
            )
            response_dict = response.model_dump()
            #logger.debug(f"API response: {response_dict}")
            return response_dict
        except Exception as e:
            logger.error(f"Error in API call: {e}")
            return {"error": str(e)}
    
    # def summarize_story(self, story: Dict[str, Any]) -> str:
    #     messages = [
    #         {"role": "system", "content": "You are an AI assistant specialized in summarizing  Cyber Security news."},
    #         {"role": "user", "content": 
    #         f"""Please analyze the following Cyber Security news and structure your summary in JSON format with the following elements:
    #             {{
    #                 "title": "The title of the story",
    #                 "author": "The author of the story",
    #                 "overview": "A concise overview of the story's main points in 2-3 sentences",
    #                 "key_topics": [
    #                     "Topic 1",
    #                     "Topic 2",
    #                     "Topic 3"
    #                 ],
    #                 "potential_impact": "Brief description of the story's potential impact or significance"
    #             }}

    #             Here's the story to analyze:
    #             {json.dumps(story)}
    #         """
    #         }
    #     ]
    #     result = self.call_api(messages)
    #     if "choices" in result and len(result["choices"]) > 0:
    #         return result["choices"][0]["message"]["content"]
    #     return ""
    
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
        #logger.debug(f"Analyzing query: {query}")
        messages = [
            {"role": "system", "content": "You are an intelligent AI assistant specialized in analyzing user queries about Cyber Security news."},
            {"role": "user", "content": 
             f"""Analyze the following user query and provide search results:
                1. At least 3 key points to look for in Cyber Security news
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
    
    def hybrid_search(self, query_embedding: List[float], keywords: List[str], vector_db, n_results: int = 5) -> List[Dict[str, Any]]:
        #logger.debug(f"Performing hybrid search with query embedding length: {len(query_embedding)} and keywords: {keywords}")
        
        # Perform semantic search
        try:
            semantic_results = vector_db.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 2,
                include=["documents", "metadatas", "distances"]
            )
            #logger.debug("Semantic search successful")
        except Exception as e:
            logger.error(f"Semantic search failed with error: {str(e)}")
            semantic_results = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        # Perform keyword search
        try:
            keyword_query = " OR ".join(keywords)
            keyword_results = vector_db.collection.query(
                query_texts=[keyword_query],
                n_results=n_results * 2,
                include=["documents", "metadatas", "distances"]
            )
            #logger.debug("Keyword search successful")
        except Exception as e:
            logger.error(f"Keyword search failed with error: {str(e)}")
            keyword_results = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        # Combine and re-rank results
        combined_results = []
        seen_ids = set()

        for sem_idx, key_idx in zip(range(len(semantic_results['ids'][0])), range(len(keyword_results['ids'][0]))):
            if sem_idx < len(semantic_results['ids'][0]):
                sem_id = semantic_results['ids'][0][sem_idx]
                if sem_id not in seen_ids:
                    seen_ids.add(sem_id)
                    try:
                        document = json.loads(semantic_results['documents'][0][sem_idx])
                    except json.JSONDecodeError:
                        document = semantic_results['documents'][0][sem_idx]
                    combined_results.append({
                        'id': sem_id,
                        'document': document,
                        'metadata': semantic_results['metadatas'][0][sem_idx],
                        'score': 0.7 * (1 - semantic_results['distances'][0][sem_idx])
                    })

            if key_idx < len(keyword_results['ids'][0]):
                key_id = keyword_results['ids'][0][key_idx]
                if key_id not in seen_ids:
                    seen_ids.add(key_id)
                    try:
                        document = json.loads(keyword_results['documents'][0][key_idx])
                    except json.JSONDecodeError:
                        document = keyword_results['documents'][0][key_idx]
                    combined_results.append({
                        'id': key_id,
                        'document': document,
                        'metadata': keyword_results['metadatas'][0][key_idx],
                        'score': 0.3 * (1 - keyword_results['distances'][0][key_idx])
                    })

        # Sort by score and return top n_results
        combined_results.sort(key=lambda x: x['score'], reverse=True)
        return combined_results[:n_results]
    
    def generate_response(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        context = "\n".join([f"Story {i+1}: {json.dumps(result)}" for i, result in enumerate(search_results)])
        
        messages = [
            {"role": "system", "content": "You are an intelligent AI assistant specialized in answering questions about Cyber Security news"},
            {"role": "user", "content": 
             f"""Answer the following query based on the provided Cyber Security news. Focus on extracting and presenting specific information from the stories.
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


    # def process_query(self, query: str, vector_db) -> Dict[str, Any]:
    #     #logger.debug(f"Processing query: {query}")
        
    #     analysis = self.analyze_user_query(query)
    #     query_embedding = self.embed_query(query)
        
    #     #logger.debug("Performing hybrid search")
    #     search_results = self.hybrid_search(
    #         query_embedding=query_embedding,
    #         keywords=analysis.get('keywords', []),
    #         vector_db=vector_db,
    #         n_results=5
    #     )
        
    #     #logger.debug("Generating response")
    #     response = self.generate_response(query, search_results)

    #     final_result = {
    #         "answer": response.get('answer', "Sorry, I couldn't generate an answer."),
    #         "references": response.get('references', []),
    #         "confidence": response.get('confidence', 0.0),
    #     }
        
    #     return final_result


    def create_rag_graph(self):
        def query_analyzer(state):
            logger.debug(f"Query analyzer input state: {state}")
            try:
                query = state.get('query')
                if not query:
                    raise ValueError("Query is missing from the state")
                analysis = self.analyze_user_query(query)
                state['analysis'] = analysis
                logger.debug(f"Query analyzer output state: {state}")
                return state
            except Exception as e:
                logger.error(f"Error in query_analyzer: {e}")
                state['error'] = str(e)
                return state

        def retriever(state):
            logger.debug(f"Retriever input state: {state}")
            try:
                query = state.get('query')
                analysis = state.get('analysis', {})
                vector_db = state.get('vector_db')
                if not query or not vector_db:
                    raise ValueError("Query or vector_db is missing from the state")
                query_embedding = self.embed_query(query)
                keywords = analysis.get('keywords', [])
                search_results = self.hybrid_search(query_embedding, keywords, vector_db)
                state['search_results'] = search_results
                logger.debug(f"Retriever output state: {state}")
                return state
            except Exception as e:
                logger.error(f"Error in retriever: {e}")
                state['error'] = str(e)
                return state

        def generator(state):
            logger.debug(f"Generator input state: {state}")
            try:
                query = state.get('query')
                search_results = state.get('search_results', [])
                if not query:
                    raise ValueError("Query is missing from the state")
                response = self.generate_response(query, search_results)
                state['response'] = response
                logger.debug(f"Generator output state: {state}")
                return state
            except Exception as e:
                logger.error(f"Error in generator: {e}")
                state['error'] = str(e)
                return state

        workflow = Graph()
        workflow.add_node("query_analyzer", query_analyzer)
        workflow.add_node("retriever", retriever)
        workflow.add_node("generator", generator)

        workflow.set_entry_point("query_analyzer")
        workflow.add_edge("query_analyzer", "retriever")
        workflow.add_edge("retriever", "generator")
        workflow.add_edge("generator", END)

        return workflow.compile()
    
    def check_groundedness(self, context: str, response: str) -> Dict[str, Any]:
        try:
            completion = self.client.chat.completions.create(
                model="solar-1-mini-groundedness-check",
                messages=[
                    {"role": "user", "content": context},
                    {"role": "assistant", "content": response}
                ]
            )
            
            result = json.loads(completion.choices[0].message.content)
            return {
                "score": result.get("score", 0.0),
                "feedback": result.get("feedback", "")
            }
        except Exception as e:
            print(f"Error in groundedness check: {e}")
            return {"score": 0.0, "feedback": "Error in groundedness check"}

    def process_query(self, query: str, vector_db) -> Dict[str, Any]:
        try:
            initial_state = {
                "query": query,
                "vector_db": vector_db,
            }
            logger.debug(f"Initial state: {initial_state}")

            final_state = self.graph.invoke(initial_state)
            logger.debug(f"Final state: {final_state}")

            if 'response' in final_state:
                return final_state['response']
            elif 'error' in final_state:
                return {
                    "answer": f"An error occurred: {final_state['error']}",
                    "references": [],
                    "confidence": 0.0
                }

            logger.error("Graph execution completed")
            return {
                "answer": "Sorry, I couldn't generate a response due to an unknown error.",
                "references": [],
                "confidence": 0.0
            }
        except Exception as e:
            logger.error(f"Error in process_query: {e}")
            return {
                "answer": f"An error occurred while processing your query: {str(e)}",
                "references": [],
                "confidence": 0.0
            }
solar_hn = SolarHackerNews()

    