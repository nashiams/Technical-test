import os
import pickle
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

print("=" * 60)
print("☁️ Initializing Google Drive API (OAuth)...")
print("=" * 60)

# Scopes for Drive access
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Token file path
TOKEN_PATH = os.getenv('GOOGLE_TOKEN_PATH', '/app/token/token.pickle')
CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', '/app/credentials.json')
GOOGLE_DRIVE_FOLDER_ID = os.getenv("FOLDER_ID", "")

print(f"📁 Credentials: {CREDENTIALS_PATH}")
print(f"🔑 Token: {TOKEN_PATH}")
print(f"📁 Folder ID: {GOOGLE_DRIVE_FOLDER_ID}")

def get_credentials():
    """Get valid user credentials from storage"""
    creds = None
    
    # Load existing token
    if os.path.exists(TOKEN_PATH):
        print("🔑 Loading existing token...")
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
        print("✅ Token loaded")
    
    # Refresh if expired
    if creds and not creds.valid:
        if creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
            print("✅ Token refreshed")
            
            # Save refreshed credentials
            os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
            with open(TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)
                print("💾 Token saved")
        else:
            print("❌ Token expired and no refresh_token!")
            return None
    
    return creds

# Initialize Drive service
try:
    credentials = get_credentials()
    
    if credentials:
        drive_service = build('drive', 'v3', credentials=credentials)
        print("✅ Google Drive API initialized (OAuth)")
        
        if GOOGLE_DRIVE_FOLDER_ID:
            print(f"📁 Using folder ID: {GOOGLE_DRIVE_FOLDER_ID}")
        else:
            print("⚠️ No FOLDER_ID set - will upload to root 'My Drive'")
    else:
        drive_service = None
        print("⚠️ No credentials - worker will use fallback storage")
        print("💡 Authorize via: http://localhost:8000/authorize")
    
    print("=" * 60 + "\n")
    
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    import traceback
    traceback.print_exc()
    drive_service = None
