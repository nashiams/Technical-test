#!/usr/bin/env python3
"""Test Google Drive API access"""

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
CREDENTIALS_PATH = "./storage-faceswap-1-2981685d4204.json"
FOLDER_ID = "1EaHz2sOPVVHEDhRCb9d3Gaol82FYeM0m"

print("=" * 60)
print("🧪 Testing Google Drive API Access")
print("=" * 60)

try:
    # Load credentials
    print(f"\n🔑 Loading credentials from: {CREDENTIALS_PATH}")
    SCOPES = ['https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH, 
        scopes=SCOPES
    )
    print("✅ Credentials loaded")
    
    # Build service
    print("🔌 Building Drive service...")
    drive_service = build('drive', 'v3', credentials=credentials)
    print("✅ Service built")
    
    # Test: Get folder info
    print(f"\n📁 Testing access to folder: {FOLDER_ID}")
    try:
        folder_info = drive_service.files().get(
            fileId=FOLDER_ID,
            fields='id, name, capabilities, owners, permissions'
        ).execute()
        
        print(f"✅ Folder found: {folder_info.get('name')}")
        print(f"📂 Folder ID: {folder_info.get('id')}")
        
        capabilities = folder_info.get('capabilities', {})
        print(f"\n🔐 Capabilities:")
        print(f"  Can read: {capabilities.get('canReadRevisions', False)}")
        print(f"  Can edit: {capabilities.get('canEdit', False)}")
        print(f"  Can share: {capabilities.get('canShare', False)}")
        print(f"  Can create: {capabilities.get('canAddChildren', False)}")
        
        if not capabilities.get('canEdit'):
            print("\n❌ ERROR: Service account CANNOT edit this folder!")
            print("💡 Solution: Share the folder with Editor permission to:")
            print("   storage-faceswap@storage-faceswap-1.iam.gserviceaccount.com")
        else:
            print("\n✅ Service account HAS edit access!")
            
    except HttpError as e:
        print(f"❌ HTTP Error {e.resp.status}: {e}")
        if e.resp.status == 404:
            print("💡 Folder not found - check FOLDER_ID")
        elif e.resp.status == 403:
            print("💡 Permission denied - service account needs access")
    
    # Test: Create a test file
    if capabilities.get('canEdit'):
        print("\n📤 Testing file upload...")
        test_file_metadata = {
            'name': 'test_upload.txt',
            'parents': [FOLDER_ID],
        }
        
        from googleapiclient.http import MediaInMemoryUpload
        media = MediaInMemoryUpload(
            b'This is a test file from the Face Swap worker',
            mimetype='text/plain'
        )
        
        file = drive_service.files().create(
            body=test_file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()
        
        print(f"✅ Test file created: {file.get('name')}")
        print(f"📁 File ID: {file.get('id')}")
        print(f"🔗 View link: {file.get('webViewLink')}")
        
        # Make it public
        print("\n🔓 Making file public...")
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        drive_service.permissions().create(
            fileId=file.get('id'),
            body=permission
        ).execute()
        
        direct_link = f"https://drive.google.com/uc?export=view&id={file.get('id')}"
        print(f"✅ Public link: {direct_link}")
        
        print("\n🎉 SUCCESS! Google Drive is working correctly!")
        print(f"💡 You can delete the test file from: {file.get('webViewLink')}")
        
except FileNotFoundError:
    print(f"❌ Credentials file not found: {CREDENTIALS_PATH}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
