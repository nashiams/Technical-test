import os
import pickle
from flask import request, redirect, jsonify
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# OAuth configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', '/app/credentials.json')
TOKEN_PATH = os.getenv('GOOGLE_TOKEN_PATH', '/app/token/token.pickle')
REDIRECT_URI = 'http://localhost:8000/oauth2callback'

def register_oauth_routes(app):
    """Register OAuth routes with Flask app"""
    
    @app.route("/authorize", methods=["GET"])
    def authorize():
        """Step 1: Initiate OAuth flow"""
        try:
            if not os.path.exists(CREDENTIALS_PATH):
                return jsonify({
                    "error": "credentials.json not found",
                    "path": CREDENTIALS_PATH,
                    "solution": "Mount credentials.json to /app/credentials.json"
                }), 404
            
            # Create flow instance
            flow = Flow.from_client_secrets_file(
                CREDENTIALS_PATH,
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
            
            # Generate authorization URL
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            return jsonify({
                "message": "Click the URL to authorize",
                "authorization_url": authorization_url,
                "state": state,
                "instructions": "1. Click authorization_url, 2. Login with Gmail, 3. You'll be redirected back"
            }), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/oauth2callback", methods=["GET"])
    def oauth2callback():
        """Step 2: OAuth callback"""
        try:
            code = request.args.get('code')
            if not code:
                return jsonify({"error": "No authorization code received"}), 400
            
            # Exchange code for credentials
            flow = Flow.from_client_secrets_file(
                CREDENTIALS_PATH,
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
            
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Save credentials
            os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
            with open(TOKEN_PATH, 'wb') as token:
                pickle.dump(credentials, token)
            
            # Test the credentials
            drive_service = build('drive', 'v3', credentials=credentials)
            about = drive_service.about().get(fields="user").execute()
            user_email = about.get('user', {}).get('emailAddress', 'Unknown')
            
            return jsonify({
                "message": "✅ Authorization successful!",
                "user": user_email,
                "token_saved": TOKEN_PATH,
                "next_step": "Restart worker: docker-compose restart worker"
            }), 200
            
        except Exception as e:
            import traceback
            return jsonify({
                "error": str(e),
                "traceback": traceback.format_exc()
            }), 500
    
    @app.route("/oauth_status", methods=["GET"])
    def oauth_status():
        """Check if OAuth token exists and is valid"""
        try:
            if not os.path.exists(TOKEN_PATH):
                return jsonify({
                    "authorized": False,
                    "message": "No token found. Visit /authorize to login",
                    "token_path": TOKEN_PATH
                }), 200
            
            # Load and check token
            with open(TOKEN_PATH, 'rb') as token:
                creds = pickle.load(token)
            
            if creds.valid:
                drive_service = build('drive', 'v3', credentials=creds)
                about = drive_service.about().get(fields="user").execute()
                user_email = about.get('user', {}).get('emailAddress')
                
                return jsonify({
                    "authorized": True,
                    "user": user_email,
                    "message": "Token is valid",
                    "worker_ready": True
                }), 200
            else:
                return jsonify({
                    "authorized": False,
                    "message": "Token expired. Visit /authorize to re-login"
                }), 200
                
        except Exception as e:
            return jsonify({
                "authorized": False,
                "error": str(e)
            }), 500
