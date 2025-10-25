import os
import shutil
import time
from google_drive_oauth import drive_service, GOOGLE_DRIVE_FOLDER_ID
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

def upload_to_google_drive(file_path, jobId, max_retries=3):
    """Upload result image to Google Drive with retry logic"""
    
    for attempt in range(max_retries):
        try:
            # Check if drive_service is initialized
            if drive_service is None:
                print("⚠️ Google Drive not initialized - using fallback")
                return fallback_to_local(file_path, jobId)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Result file not found: {file_path}")
            
            # Verify file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise ValueError(f"Result file is empty: {file_path}")
            

            
            # Prepare file metadata
            file_metadata = {
                'name': f'{jobId}.jpg',
                'parents': [GOOGLE_DRIVE_FOLDER_ID],
                'description': f'Face swap result for job {jobId}',
            }
            
            # Upload file with chunked upload for large files
            media = MediaFileUpload(
                file_path,
                mimetype='image/jpeg',
                resumable=True,
            )
            
            
            file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink, webContentLink, name'
            ).execute()
            
            file_id = file.get('id')
            
            
            # Make file publicly accessible
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            drive_service.permissions().create(
                fileId=file_id,
                body=permission,
                fields='id'
            ).execute()
            
            # Use direct download link (converts to image automatically)
            result_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            
 
            return result_url
            
        except BrokenPipeError as e:
            print(f"❌ BrokenPipeError on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"🔄 Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                print("❌ Max retries reached, using fallback")
                return fallback_to_local(file_path, jobId)
        
        except (ConnectionError, TimeoutError, OSError) as e:
            print(f"❌ Network error on attempt {attempt + 1}: {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"🔄 Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                return fallback_to_local(file_path, jobId)
                
        except HttpError as e:
            error_details = e.error_details if hasattr(e, 'error_details') else str(e)
            print(f"❌ Google Drive HTTP Error: {e.resp.status} - {error_details}")
            
            if e.resp.status in [500, 502, 503, 504] and attempt < max_retries - 1:
                # Server errors - retry
                wait_time = 2 ** attempt
                print(f"🔄 Server error, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                return fallback_to_local(file_path, jobId)
                
        except Exception as e:
            print(f"❌ Upload error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return fallback_to_local(file_path, jobId)
    
    # Should never reach here, but just in case
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
    
    return fallback_url

def cleanup_job_files(jobId, img1_path=None, img2_path=None, result_path=None):
    """Clean up all temporary files for a job"""
    try:
        # Remove job directory (contains result and possibly uploaded images)
        job_dir = f"/tmp/{jobId}"
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir, ignore_errors=True)
        
        # Remove individual files if they exist outside job dir
        for file_path in [img1_path, img2_path, result_path]:
            if file_path and os.path.exists(file_path):
                try:
                    # Check if file is not inside job_dir to avoid double deletion
                    if not file_path.startswith(job_dir):
                        os.remove(file_path)
                except Exception as err:
                    print(f"Could not remove {file_path}: {err}")
                    
    except Exception as e:
        print(f" Cleanup error for job {jobId}: {e}")