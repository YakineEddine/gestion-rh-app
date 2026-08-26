"""
Tests unitaires pour l'Assistant IA de generation de clauses contractuelles.
"""
import unittest
from unittest.mock import patch, MagicMock
from app.core import ai_service


class TestAIService(unittest.TestCase):

    def test_prompt_empty(self):
        with self.assertRaises(ValueError):
            ai_service.generate_clause("   ")

    def test_unconfigured_service(self):
        with patch.object(ai_service, "get_config", return_value={
            "provider": "grok", "api_key": "", "model": "grok-4.3",
            "base_url": "https://api.x.ai/v1", "timeout": 30
        }):
            with self.assertRaises(RuntimeError):
                ai_service.generate_clause("Clause de test")

    def test_grok_successful_mock(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"title": "Clause de télétravail", "content": "Article sur le télétravail...", "category": "Télétravail"}'
                }
            }]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(ai_service, "get_config", return_value={
            "provider": "grok", "api_key": "dummy_key", "model": "grok-4.3",
            "base_url": "https://api.x.ai/v1", "timeout": 30
        }), patch("httpx.Client.post", return_value=mock_response):
            result = ai_service.generate_clause("Rédige une clause de télétravail")
            self.assertEqual(result["title"], "Clause de télétravail")
            self.assertEqual(result["content"], "Article sur le télétravail...")
            self.assertEqual(result["category"], "Télétravail")

    def test_grok_json_with_markdown_fence(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '```json\n{"title": "Clause de confidentialité", "content": "Secret pro...", "category": "Confidentialité"}\n```'
                }
            }]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(ai_service, "get_config", return_value={
            "provider": "grok", "api_key": "dummy_key", "model": "grok-4.3",
            "base_url": "https://api.x.ai/v1", "timeout": 30
        }), patch("httpx.Client.post", return_value=mock_response):
            result = ai_service.generate_clause("Clause de confidentialité")
            self.assertEqual(result["title"], "Clause de confidentialité")
            self.assertEqual(result["category"], "Confidentialité")


if __name__ == "__main__":
    unittest.main()
