import unittest
from unittest.mock import patch, MagicMock
from src.services.chat import SolarHackerNews
import json

class TestSolarHackerNews(unittest.TestCase):

    def setUp(self):
        self.solar_hn = SolarHackerNews()
        self.mock_vector_db = MagicMock()

    @patch('src.services.chat.OpenAI')
    def test_embed_query(self, mock_openai):
        # Create a mock embedding of the correct length (4096 for Solar model)
        mock_embedding = [0.01] * 4096
        mock_openai.return_value.embeddings.create.return_value.data = [MagicMock(embedding=mock_embedding)]
        
        result = self.solar_hn.embed_query("Test query")
        
        # Check if the result is a list
        self.assertIsInstance(result, list)
        
        # Check if the result has the correct length
        self.assertEqual(len(result), 4096)
        
        # Check if all elements are floats
        self.assertTrue(all(isinstance(x, float) for x in result))
        
        # Check if the values are within a reasonable range (between -1 and 1)
        self.assertTrue(all(-1 <= x <= 1 for x in result))

    @patch('src.services.chat.OpenAI')
    def test_embed_document(self, mock_openai):
        # Create a mock embedding of the correct length (4096 for Solar model)
        mock_embedding = [0.01] * 4096
        mock_openai.return_value.embeddings.create.return_value.data = [MagicMock(embedding=mock_embedding)]
        
        result = self.solar_hn.embed_document("Test document")
        
        # Check if the result is a list
        self.assertIsInstance(result, list)
        
        # Check if the result has the correct length
        self.assertEqual(len(result), 4096)
        
        # Check if all elements are floats
        self.assertTrue(all(isinstance(x, float) for x in result))
        
        # Check if the values are within a reasonable range (between -1 and 1)
        self.assertTrue(all(-1 <= x <= 1 for x in result))

    @patch('src.services.chat.SolarHackerNews.call_api')
    def test_analyze_user_query_good(self, mock_call_api):
        mock_call_api.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "key_points": ["point1", "point2", "point3"],
                        "related_topics": ["topic1", "topic2"],
                        "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
                    })
                }
            }]
        }
        result = self.solar_hn.analyze_user_query("What are the latest trends in ransomware attacks?")
        self.assertIn("key_points", result)
        self.assertIn("related_topics", result)
        self.assertIn("keywords", result)

    @patch('src.services.chat.SolarHackerNews.call_api')
    def test_analyze_user_query_bad(self, mock_call_api):
        mock_call_api.return_value = {"error": "API error"}
        result = self.solar_hn.analyze_user_query("How do I hack into my neighbor's Wi-Fi?")
        self.assertEqual(result, {"key_points": [], "related_topics": [], "keywords": []})

    @patch('src.services.chat.SolarHackerNews.call_api')
    def test_generate_response_good(self, mock_call_api):
        mock_call_api.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "answer": "This is a test answer",
                        "references": [{"story_id": "123", "relevance": "High"}],
                        "confidence": 0.8
                    })
                }
            }]
        }
        result = self.solar_hn.generate_response("Explain zero-day vulnerabilities", [{"id": "123", "document": "Test doc"}])
        self.assertIn("answer", result)
        self.assertIn("references", result)
        self.assertIn("confidence", result)

    @patch('src.services.chat.SolarHackerNews.call_api')
    def test_generate_response_bad(self, mock_call_api):
        mock_call_api.return_value = {"error": "API error"}
        result = self.solar_hn.generate_response("What's your opinion on government surveillance?", [])
        self.assertEqual(result["answer"], "Sorry, I couldn't generate a response due to an error.")

    @patch('src.services.chat.SolarHackerNews.analyze_user_query')
    @patch('src.services.chat.SolarHackerNews.embed_query')
    @patch('src.services.chat.SolarHackerNews.hybrid_search')
    @patch('src.services.chat.SolarHackerNews.generate_response')
    def test_process_query_good(self, mock_generate, mock_hybrid, mock_embed, mock_analyze):
        mock_analyze.return_value = {"keywords": ["test"]}
        mock_embed.return_value = [0.1, 0.2, 0.3]
        mock_hybrid.return_value = [{"id": "123", "document": "Test doc"}]
        mock_generate.return_value = {
            "answer": "Test answer",
            "references": [{"story_id": "123", "relevance": "High"}],
            "confidence": 0.9
        }
        result = self.solar_hn.process_query("How do AI and machine learning impact cybersecurity?", self.mock_vector_db)
        self.assertIn("answer", result)
        self.assertIn("references", result)
        self.assertIn("confidence", result)

    @patch('src.services.chat.SolarHackerNews.analyze_user_query')
    @patch('src.services.chat.SolarHackerNews.embed_query')
    @patch('src.services.chat.SolarHackerNews.hybrid_search')
    @patch('src.services.chat.SolarHackerNews.generate_response')
    def test_process_query_bad(self, mock_generate, mock_hybrid, mock_embed, mock_analyze):
        mock_analyze.return_value = {"keywords": []}
        mock_embed.return_value = []
        mock_hybrid.return_value = []
        mock_generate.return_value = {
            "answer": "Sorry, I couldn't generate an answer.",
            "references": [],
            "confidence": 0.0
        }
        result = self.solar_hn.process_query("Can you give me Mark Zuckerberg's password?", self.mock_vector_db)
        self.assertEqual(result["answer"], "Sorry, I couldn't generate an answer.")
        self.assertEqual(result["references"], [])
        self.assertEqual(result["confidence"], 0.0)

    @patch('src.services.chat.SolarHackerNews.embed_query')
    def test_hybrid_search(self, mock_embed_query):
        self.solar_hn = SolarHackerNews()
        mock_vector_db = MagicMock()

        # Mock the embed_query method
        mock_embed_query.return_value = [0.1] * 4096

        # Mock the vector_db.collection.query method
        mock_vector_db.collection.query.side_effect = [
            # Semantic search results
            {
                "ids": [["sem1", "sem2"]],
                "documents": [["Semantic doc 1", "Semantic doc 2"]],
                "metadatas": [[{"source": "sem1"}, {"source": "sem2"}]],
                "distances": [[0.1, 0.2]]
            },
            # Keyword search results
            {
                "ids": [["key1", "key2"]],
                "documents": [["Keyword doc 1", "Keyword doc 2"]],
                "metadatas": [[{"source": "key1"}, {"source": "key2"}]],
                "distances": [[0.3, 0.4]]
            }
        ]

        query_embedding = [0.1] * 4096
        keywords = ["test", "keyword"]
        
        results = self.solar_hn.hybrid_search(query_embedding, keywords, mock_vector_db, n_results=2)

        # Check if the results are correct
        self.assertEqual(len(results), 2)
        self.assertIn(results[0]['id'], ["sem1", "key1"])
        self.assertIn(results[1]['id'], ["sem2", "key2"])
        self.assertTrue(all('score' in result for result in results))
        self.assertTrue(results[0]['score'] >= results[1]['score'])  # Check if results are sorted
        self.assertTrue(isinstance(results[0]['document'], str))  # Check if document is a string
        
    @patch('src.services.chat.SolarHackerNews.embed_query')
    def test_hybrid_search_error_handling(self, mock_embed_query):
        self.solar_hn = SolarHackerNews()
        mock_vector_db = MagicMock()

        # Mock the embed_query method
        mock_embed_query.return_value = [0.1] * 4096

        # Mock the vector_db.collection.query method to raise an exception
        mock_vector_db.collection.query.side_effect = Exception("Database error")

        query_embedding = [0.1] * 4096
        keywords = ["test", "keyword"]
        
        results = self.solar_hn.hybrid_search(query_embedding, keywords, mock_vector_db, n_results=2)

        # Check if the method handles errors 
        self.assertEqual(results, [])

if __name__ == '__main__':
    unittest.main()

## python -m unittest test_hackernews_chat.py