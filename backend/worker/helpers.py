import os
import shutil
from google_drive_oauth import drive_service, GOOGLE_DRIVE_FOLDER_ID
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

def upload_to_google_drive(file_path, jobId):
    """Upload result image to Google Drive"""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Result file not found: {file_path}")
        
        # Verify file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError(f"Result file is empty: {file_path}")
        
        print(f"📤 Uploading {file_size} bytes to Google Drive...")
        print(f"📁 Target folder ID: {GOOGLE_DRIVE_FOLDER_ID}")
        
        # Prepare file metadata
        file_metadata = {
            'name': f'{jobId}.jpg',
            'parents': [GOOGLE_DRIVE_FOLDER_ID],
            'description': f'Face swap result for job {jobId}',
        }
        
        # Upload file
        media = MediaFileUpload(
            file_path,
            mimetype='image/jpeg',
            resumable=True
        )
        
        print("🔄 Creating file in Google Drive...")
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink, webContentLink, name'
        ).execute()
        
        file_id = file.get('id')
        file_name = file.get('name')
        
        print(f"✅ File created: {file_name} (ID: {file_id})")
        
        # Make file publicly accessible
        print("🔓 Making file public...")
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        drive_service.permissions().create(
            fileId=file_id,
            body=permission,
            fields='id'
        ).execute()
        
        # Get direct view link
        result_url = f"https://drive.google.com/uc?export=view&id={file_id}"
        
        print(f"✅ Uploaded to Google Drive: {result_url}")
        print(f"📁 File ID: {file_id}")
        print(f"🔗 View link: https://drive.google.com/file/d/{file_id}/view")
        
        return result_url
        
    except HttpError as e:
        error_details = e.error_details if hasattr(e, 'error_details') else str(e)
        print(f"❌ Google Drive HTTP Error: {e.resp.status} - {error_details}")
        
        if e.resp.status == 403:
            print("⚠️ Permission denied!")
            print(f"📧 Service account: storage-faceswap@storage-faceswap-1.iam.gserviceaccount.com")
            print(f"📁 Folder ID: {GOOGLE_DRIVE_FOLDER_ID}")
            print("💡 Solutions:")
            print("   1. Share folder with service account (Editor role)")
            print("   2. Or remove FOLDER_ID from .env to auto-create")
        elif e.resp.status == 404:
            print("⚠️ Folder not found! Check FOLDER_ID or remove it to auto-create.")
            
        # Fall back to local storage
        return fallback_to_local(file_path, jobId)
        
    except Exception as e:
        print(f"❌ Google Drive upload error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
        # Fall back to local storage
        return fallback_to_local(file_path, jobId)

def fallback_to_local(file_path, jobId):
    """Fallback: Save to shared volume and return API URL"""
    print(f"⚠️ Falling back to local storage...")
    
    results_dir = "/tmp/results"
    os.makedirs(results_dir, exist_ok=True)
    
    fallback_path = os.path.join(results_dir, f"{jobId}.jpg")
    shutil.copy2(file_path, fallback_path)
    
    # Return URL that API can serve
    fallback_url = f"http://api:5000/results/{jobId}.jpg"
    print(f"💾 Saved locally: {fallback_path}")
    print(f"🔗 Fallback URL: {fallback_url}")
    
    return fallback_url

def cleanup_job_files(jobId, img1_path=None, img2_path=None, result_path=None):
    """Clean up all temporary files for a job"""
    try:
        # Remove job directory (contains result and possibly uploaded images)
        job_dir = f"/tmp/{jobId}"
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir, ignore_errors=True)
            print(f"🧹 Cleaned up job directory: {job_dir}")
        
        # Remove individual files if they exist outside job dir
        for file_path in [img1_path, img2_path, result_path]:
            if file_path and os.path.exists(file_path):
                try:
                    # Check if file is not inside job_dir to avoid double deletion
                    if not file_path.startswith(job_dir):
                        os.remove(file_path)
                        print(f"🧹 Removed file: {file_path}")
                except Exception as err:
                    print(f"⚠️ Could not remove {file_path}: {err}")
                    
        print(f"✅ Cleanup completed for job {jobId}")
    except Exception as e:
        print(f"⚠️ Cleanup error for job {jobId}: {e}")