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
    
    def analyze_user_query(self, query: str) -> Dict[str, Any]:
        #logger.debug(f"Analyzing query: {query}")
        messages = [
            {"role": "system", "content": "You are an intelligent AI assistant specialized in analyzing user queries about Cyber Security-related information."},
            {"role": "user", "content": 
             f"""Analyze the following user query and provide search results:
                1. At least 3 key points to look for in Cyber Security information
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
            {"role": "system", "content": "You are an intelligent AI assistant named Wolfare specialized in answering questions about Cyber Security."},
            {"role": "user", "content": 
             f"""Wolfare can answer the following query based on the provided Cyber Security news, trends, manual, techniques, vulnerabilities and information.. Focus on extracting and presenting specific information from the news and various sources.
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
            
                Rules:
                1. Your entire response must be a valid JSON object.
                2. The "answer" field should contain your detailed response to the user's query.
                3. The "references" field should be an array of objects, each containing "document" and "relevance" fields.
                4. The "confidence" field should be a number between 0 and 1, indicating your confidence in the answer.
                5. Ensure all JSON syntax is correct, including quotes around strings and proper use of commas.
                6. Do not include any text outside of the JSON object in your response.
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
            logger.error(f"Error in groundedness check: {e}")
            return {"score": 0.0, "feedback": "Error in groundedness check"}

    def self_evaluate(self, query: str, response: Dict[str, Any], search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        context = "\n".join([f"Document {i+1}: {result['document']}" for i, result in enumerate(search_results)])
        
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in evaluating responses to cyber security-related queries."},
            {"role": "user", "content": 
             f"""Evaluate the following response to the user query. Consider the relevance, accuracy, and completeness of the answer based on the provided context.

                User query: {query}

                Context:
                {context}

                Response:
                {json.dumps(response, indent=2)}

                Provide your evaluation in JSON format:
                {{
                    "evaluation_score": 0.0,  
                    "feedback": "Your detailed feedback here",
                    "suggestions_for_improvement": ["suggestion1", "suggestion2"]
                }}
                // evaluation_score should be between 0 and 1
             """
            }
        ]
        result = self.call_api(messages)
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            try:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    return json.loads(json_str)
                else:
                    raise ValueError("No JSON object found in the response")
            except json.JSONDecodeError as e:
                logger.error(f"JSON Decode Error: {e}")
                logger.error(f"Problematic content: {content}")
            except ValueError as e:
                logger.error(f"Value Error: {e}")
                logger.error(f"Problematic content: {content}")
            
            return {
                "evaluation_score": 0.5,
                "feedback": "Unable to parse evaluation. Please check the response format.",
                "suggestions_for_improvement": ["Ensure the response is in correct JSON format"]
            }
        
        return {"evaluation_score": 0.0, "feedback": "Unable to evaluate", "suggestions_for_improvement": []}
    
    
    def create_rag_graph(self):
        def query_analyzer(state):
            #logger.debug(f"Query analyzer input state: {state}")
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
            #logger.debug(f"Retriever input state: {state}")
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
            #logger.debug(f"Generator input state: {state}")
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

        def hallucination_checker(state):
            #logger.debug(f"Groundedness checker input state: {state}")
            try:
                query = state.get('query')
                response = state.get('response', {})
                search_results = state.get('search_results', [])
                context = "\n".join([f"Document {i+1}: {result['document']}" for i, result in enumerate(search_results)])
                groundedness = self.check_groundedness(context, response.get('answer', ''))
                state['groundedness'] = groundedness
                logger.debug(f"Groundedness checker output state: {state}")
                return state
            except Exception as e:
                logger.error(f"Error in groundedness_checker: {e}")
                state['error'] = str(e)
                return state

        def evaluator(state):
            #logger.debug(f"Evaluator input state: {state}")
            try:
                query = state.get('query')
                response = state.get('response', {})
                search_results = state.get('search_results', [])
                evaluation = self.self_evaluate(query, response, search_results)
                state['evaluation'] = evaluation
                logger.debug(f"Evaluator output state: {state}")
                return state
            except Exception as e:
                logger.error(f"Error in evaluator: {e}")
                state['error'] = str(e)
                return state

        workflow = Graph()
        workflow.add_node("query_analyzer", query_analyzer)
        workflow.add_node("retriever", retriever)
        workflow.add_node("generator", generator)
        workflow.add_node("groundedness_checker", hallucination_checker)
        workflow.add_node("evaluator", evaluator)

        workflow.set_entry_point("query_analyzer")
        workflow.add_edge("query_analyzer", "retriever")
        workflow.add_edge("retriever", "generator")
        workflow.add_edge("generator", "groundedness_checker")
        workflow.add_edge("groundedness_checker", "evaluator")
        workflow.add_edge("evaluator", END)

        return workflow.compile()

    def process_query(self, query: str, vector_db) -> Dict[str, Any]:
        try:
            initial_state = {
                "query": query,
                "vector_db": vector_db,
            }
            logger.debug(f"Initial state: {initial_state}")

            final_state = self.graph.invoke(initial_state)
            logger.debug(f"Final state: {final_state}")

            if 'response' in final_state and 'groundedness' in final_state and 'evaluation' in final_state:
                result = final_state['response']
                result.update({
                    "groundedness_score": final_state['groundedness']['score'],
                    "groundedness_feedback": final_state['groundedness']['feedback'],
                    "evaluation_score": final_state['evaluation']['evaluation_score'],
                    "evaluation_feedback": final_state['evaluation']['feedback'],
                    "suggestions_for_improvement": final_state['evaluation']['suggestions_for_improvement']
                })
                return result
            elif 'error' in final_state:
                return {
                    "answer": f"An error occurred: {final_state['error']}",
                    "references": [],
                    "confidence": 0.0,
                    "groundedness_score": 0.0,
                    "evaluation_score": 0.0
                }

            logger.error("Graph execution completed without producing a complete result")
            return {
                "answer": "Sorry, I couldn't generate a complete response due to an unknown error.",
                "references": [],
                "confidence": 0.0,
                "groundedness_score": 0.0,
                "evaluation_score": 0.0
            }
        except Exception as e:
            logger.error(f"Error in process_query: {e}")
            return {
                "answer": f"An error occurred while processing your query: {str(e)}",
                "references": [],
                "confidence": 0.0,
                "groundedness_score": 0.0,
                "evaluation_score": 0.0
            }
solar_hn = SolarHackerNews()

    