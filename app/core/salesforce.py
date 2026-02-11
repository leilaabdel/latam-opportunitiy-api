# app/core/salesforce.py
import requests
import secrets
import hashlib
import base64
from urllib.parse import urlencode
from cryptography.fernet import Fernet
from typing import Dict, Tuple
from fastapi import HTTPException
from .config import settings

class SalesforceOAuth:
    """Handles Salesforce OAuth 2.0 with PKCE"""
    
    def __init__(self):
        self.client_id = settings.SALESFORCE_CLIENT_ID
        self.client_secret = settings.SALESFORCE_CLIENT_SECRET  # Still need this
        self.redirect_uri = settings.SALESFORCE_REDIRECT_URI
        self.auth_url = f"https://{settings.SALESFORCE_DOMAIN}/services/oauth2/authorize"
        self.token_url = f"https://{settings.SALESFORCE_DOMAIN}/services/oauth2/token"
        
        try:
            self.cipher = Fernet(settings.ENCRYPTION_KEY.encode())
        except Exception as e:
            raise ValueError(f"Invalid ENCRYPTION_KEY: {e}")
        
        # Store code_verifiers temporarily
        self._code_verifiers = {}
    
    def _generate_pkce_pair(self) -> Tuple[str, str]:
        """Generate PKCE code_verifier and code_challenge"""
        # Generate code_verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
        code_verifier = code_verifier.rstrip('=')
        
        # Generate code_challenge = BASE64URL(SHA256(code_verifier))
        code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
        code_challenge = code_challenge.rstrip('=')
        
        return code_verifier, code_challenge
    
    def get_auth_url(self) -> Tuple[str, str]:
        """
        Generate Salesforce OAuth URL with PKCE
        Returns: (auth_url, state)
        """
        code_verifier, code_challenge = self._generate_pkce_pair()
        state = secrets.token_urlsafe(32)
        
        # Store code_verifier
        self._code_verifiers[state] = code_verifier
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'api refresh_token',
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        return f"{self.auth_url}?{urlencode(params)}", state
    
    def exchange_code(self, code: str, state: str) -> Dict:
        """Exchange code for tokens with PKCE and client_secret"""
        code_verifier = self._code_verifiers.get(state)
        if not code_verifier:
            raise HTTPException(status_code=400, detail="Invalid state or session expired")
        
        del self._code_verifiers[state]
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,  # Include for Connected App
            'redirect_uri': self.redirect_uri,
            'code_verifier': code_verifier  # PKCE parameter
        }
        
        try:
            response = requests.post(self.token_url, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange code: {str(e)}"
            )
    
    def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh access token"""
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(self.token_url, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=401,
                detail=f"Token refresh failed: {str(e)}"
            )
    
    def encrypt(self, value: str) -> str:
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt(self, encrypted_value: str) -> str:
        try:
            return self.cipher.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

sf_oauth = SalesforceOAuth()