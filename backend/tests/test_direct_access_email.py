"""
Tests unitaires et d'intégration pour l'accès direct depuis les emails de notification.
"""
import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from jose import jwt

from app.core.security import (
    create_direct_access_token,
    verify_direct_access_token,
    SECRET_KEY,
    ALGORITHM,
)
from app.core.email_service import (
    template_contract_activated,
    template_contract_expiring_employe,
    template_contract_expired_employe,
    APP_URL,
)


class TestDirectAccessEmail(unittest.TestCase):

    def test_create_and_verify_token_valid(self):
        """Un token valide pour un employé actif est correctement décodé."""
        mock_user = MagicMock()
        mock_user.id = 42
        mock_user.email = "employe@test.com"
        mock_user.est_actif = True

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        token = create_direct_access_token(user_id=42, email="employe@test.com")
        user = verify_direct_access_token(token, mock_db)

        self.assertIsNotNone(user)
        self.assertEqual(user.id, 42)
        self.assertEqual(user.email, "employe@test.com")

    def test_verify_token_expired(self):
        """Un token expiré est rejeté."""
        mock_db = MagicMock()
        # Créer un token avec expiration passée
        expired_token = create_direct_access_token(
            user_id=42, email="employe@test.com", expires_delta=timedelta(seconds=-10)
        )
        user = verify_direct_access_token(expired_token, mock_db)
        self.assertIsNone(user)

    def test_verify_token_invalid_signature(self):
        """Un token avec une mauvaise signature est rejeté."""
        mock_db = MagicMock()
        invalid_token = jwt.encode(
            {"sub": "employe@test.com", "user_id": 42, "type": "direct_access"},
            "wrong_secret",
            algorithm=ALGORITHM
        )
        user = verify_direct_access_token(invalid_token, mock_db)
        self.assertIsNone(user)

    def test_verify_token_wrong_type(self):
        """Un token qui n'est pas de type direct_access est rejeté."""
        mock_db = MagicMock()
        wrong_type_token = jwt.encode(
            {"sub": "employe@test.com", "user_id": 42, "type": "access"},
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        user = verify_direct_access_token(wrong_type_token, mock_db)
        self.assertIsNone(user)

    def test_template_contract_expiring_includes_direct_token(self):
        """Le template d'expiration inclut le direct_token dans le bouton d'action."""
        direct_token = "mon_super_token_jwt_123"
        html = template_contract_expiring_employe(
            prenom="Jean",
            nom="Dupont",
            reference="CTR-2026-001",
            date_fin="15/09/2026",
            jours_restants=8,
            priorite="WARNING",
            direct_token=direct_token,
        )
        expected_url = f"{APP_URL}/mon-espace/contrats?direct_token={direct_token}"
        self.assertIn(expected_url, html)
        self.assertIn("Consulter mon contrat", html)

    def test_template_contract_expired_includes_direct_token(self):
        """Le template de contrat expiré inclut le direct_token."""
        direct_token = "token_expire_456"
        html = template_contract_expired_employe(
            prenom="Jean",
            nom="Dupont",
            reference="CTR-2026-001",
            date_fin="01/09/2026",
            direct_token=direct_token,
        )
        expected_url = f"{APP_URL}/mon-espace/contrats?direct_token={direct_token}"
        self.assertIn(expected_url, html)

    def test_template_contract_activated_includes_direct_token(self):
        """Le template de contrat activé inclut le direct_token."""
        direct_token = "token_actif_789"
        html = template_contract_activated(
            prenom="Jean",
            reference="CTR-2026-001",
            date_debut="01/09/2026",
            direct_token=direct_token,
        )
        expected_url = f"{APP_URL}/mon-espace/contrats?direct_token={direct_token}"
        self.assertIn(expected_url, html)


if __name__ == "__main__":
    unittest.main()
