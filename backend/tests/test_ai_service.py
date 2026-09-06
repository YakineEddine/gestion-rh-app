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


    def test_prompt_empty_structured(self):
        with self.assertRaises(ValueError):
            ai_service.generate_structured_clause("   ")

    def test_unconfigured_service_structured(self):
        with patch.object(ai_service, "get_config", return_value={
            "provider": "grok", "api_key": "", "model": "grok-4.3",
            "base_url": "https://api.x.ai/v1", "timeout": 30
        }):
            with self.assertRaises(RuntimeError):
                ai_service.generate_structured_clause("Clause de rémunération")

    def test_structured_generation_with_table(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '''{
                        "type": "mixed",
                        "title": "Rémunération et objectifs",
                        "category": "Rémunération",
                        "blocks": [
                            {
                                "type": "paragraph",
                                "content": "La rémunération comprend un fixe et un variable selon objectifs."
                            },
                            {
                                "type": "table",
                                "headers": ["Niveau d'atteinte", "Taux de prime", "Montant brut"],
                                "rows": [
                                    ["Moins de 80%", "0%", "0 DT"],
                                    ["80% à 99%", "50%", "250 DT"],
                                    ["100% et plus", "100%", "500 DT"]
                                ]
                            }
                        ]
                    }'''
                }
            }]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(ai_service, "get_config", return_value={
            "provider": "grok", "api_key": "dummy_key", "model": "grok-4.3",
            "base_url": "https://api.x.ai/v1", "timeout": 30
        }), patch("httpx.Client.post", return_value=mock_response):
            result = ai_service.generate_structured_clause("Rédige un article sur la rémunération avec prime")
            self.assertEqual(result["type"], "mixed")
            self.assertEqual(result["title"], "Rémunération et objectifs")
            self.assertEqual(len(result["blocks"]), 2)
            self.assertEqual(result["blocks"][0]["type"], "paragraph")
            self.assertEqual(result["blocks"][1]["type"], "table")
            self.assertEqual(result["blocks"][1]["headers"], ["Niveau d'atteinte", "Taux de prime", "Montant brut"])
            self.assertEqual(len(result["blocks"][1]["rows"]), 3)

    def test_structured_fallback_from_legacy_format(self):
        """Si le modèle IA retourne l'ancien format title/content, fallback propre."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"title": "Clause de non-concurrence", "content": "Le salarié s\'engage...", "category": "Obligations"}'
                }
            }]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(ai_service, "get_config", return_value={
            "provider": "grok", "api_key": "dummy_key", "model": "grok-4.3",
            "base_url": "https://api.x.ai/v1", "timeout": 30
        }), patch("httpx.Client.post", return_value=mock_response):
            result = ai_service.generate_structured_clause("Clause de non concurrence")
            self.assertEqual(result["type"], "paragraph")
            self.assertEqual(result["title"], "Clause de non-concurrence")
            self.assertEqual(len(result["blocks"]), 1)
            self.assertEqual(result["blocks"][0]["content"], "Le salarié s'engage...")

    def test_structured_to_plaintext(self):
        structured = {
            "type": "mixed",
            "blocks": [
                {"type": "paragraph", "content": "Introduction."},
                {"type": "table", "headers": ["Col 1", "Col 2"], "rows": [["Val A", "Val B"]]}
            ]
        }
        plaintext = ai_service.structured_to_plaintext(structured)
        self.assertIn("Introduction.", plaintext)
        self.assertIn("| Col 1 | Col 2 |", plaintext)
        self.assertIn("| Val A | Val B |", plaintext)

    def test_parse_structured_content(self):
        # Cas 1 : JSON structuré valide
        valid_json = '{"type": "paragraph", "blocks": [{"type": "paragraph", "content": "Test"}]}'
        parsed = ai_service.parse_structured_content(valid_json)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["type"], "paragraph")

        # Cas 2 : Texte brut classique
        plain_text = "Ceci est une clause classique en texte brut."
        self.assertIsNone(ai_service.parse_structured_content(plain_text))

        # Cas 3 : JSON invalide ou None
        self.assertIsNone(ai_service.parse_structured_content(None))
        self.assertIsNone(ai_service.parse_structured_content("{invalid json"))

    def test_document_generator_with_structured_table(self):
        """Vérifie que la génération du contrat Word supporte les articles avec tableau structuré."""
        import json
        from types import SimpleNamespace
        from datetime import date
        from app.core.document_generator import generer_contrat_word

        mock_article = SimpleNamespace(
            titre="Grille de primes d'objectifs",
            contenu_par_defaut=json.dumps({
                "type": "mixed",
                "blocks": [
                    {"type": "paragraph", "content": "Les primes sont accordées comme suit :"},
                    {
                        "type": "table",
                        "headers": ["Objectif", "Prime DT"],
                        "rows": [["Niveau A", "500 DT"], ["Niveau B", "1000 DT"]]
                    }
                ]
            })
        )

        mock_contrat = SimpleNamespace(
            reference="CTR-TEST-001",
            date_debut=date(2026, 1, 1),
            date_fin=None,
            salaire_mensuel=3500,
            employe=SimpleNamespace(
                prenom="Ali",
                nom="Ben Salah",
                matricule="EMP-100",
                poste="Ingénieur IA",
                departement="R&D"
            ),
            articles=[mock_article]
        )

        doc_buffer = generer_contrat_word(mock_contrat)
        self.assertIsNotNone(doc_buffer)
        self.assertGreater(doc_buffer.getbuffer().nbytes, 1000)


if __name__ == "__main__":
    unittest.main()

