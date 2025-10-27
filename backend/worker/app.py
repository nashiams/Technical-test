import os
import json
import pika
import requests
import redis
from pymongo import MongoClient
from datetime import datetime



# Setup environment
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://appuser:changeme123@rabbitmq:5672")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
API_UPDATE_URL = os.getenv("API_UPDATE_URL", "http://api:5000/update_status")


# Connect MongoDB
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Test connection
    client.server_info()
    db = client["face_swap"]
    jobs_collection = db["jobs"]
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    raise e

# Initialize face swap model
try:
    from face_swap import prepare_app, swap_faces
    app, swapper = prepare_app()
except Exception as e:
    import traceback
    traceback.print_exc()
    raise e

# Import helpers after models are loaded
try:
    from helpers import upload_to_google_drive, cleanup_job_files
except Exception as e:
    print(f" Failed to load helpers: {e}")
    import traceback
    traceback.print_exc()
    raise e

def process_job(job_data):
    """Process a single face swap job"""
    jobId = job_data["jobId"]
    img1_path = job_data["img1_path"]
    img2_path = job_data["img2_path"]
    sessionId = job_data.get("sessionId")
    
    # Make unique folder for this job
    job_path = f"/tmp/{jobId}"
    os.makedirs(job_path, exist_ok=True)
    result_path = os.path.join(job_path, "result.jpg")
    
    try:
        # Update MongoDB status to processing
        jobs_collection.update_one(
            {"jobId": jobId},
            {"$set": {"status": "processing", "updatedAt": datetime.utcnow()}}
        )
        
        # Perform face swap
        print(f"Processing job {jobId} for session {sessionId}")
        result_image = swap_faces(app, swapper, img1_path, img2_path)
        
        # Save result image
        from PIL import Image
        Image.fromarray(result_image).save(result_path, quality=95)
        
        # Upload to Google Drive
        result_url = upload_to_google_drive(result_path, jobId)
        
        # Update MongoDB with result
        jobs_collection.update_one(
            {"jobId": jobId},
            {"$set": {
                "status": "completed",
                "resultUrl": result_url,
                "updatedAt": datetime.utcnow()
            }}
        )
        
        # Update job status via API (this releases the session lock)
        update_data = {
            "jobId": jobId,
            "resultUrl": result_url
        }
        
        try:
            response = requests.post(API_UPDATE_URL, json=update_data, timeout=10)
            
            if response.status_code != 200:
                print(f" Failed to update job status via API: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f" Could not reach API to update status: {e}")
        
        print(f" Job {jobId} completed successfully")
        
    except Exception as e:
        error_msg = str(e)
        print(f" Job {jobId} failed: {error_msg}")
        
        # Determine error type for user-friendly messages
        if "No faces found" in error_msg:
            user_error = "No faces detected in one or both images. Please use clear photos with visible faces."
        elif "only" in error_msg and "faces" in error_msg:
            user_error = error_msg  # e.g., "The image includes only 1 faces, however, you asked for face 2"
        else:
            user_error = "Failed to process images. Please try different photos."
        
        # Update MongoDB status to failed with user-friendly error
        jobs_collection.update_one(
            {"jobId": jobId},
            {"$set": {
                "status": "failed",
                "error": user_error,
                "technicalError": error_msg,  # Keep technical details for debugging
                "updatedAt": datetime.utcnow()
            }}
        )
        
        # Notify API to release lock and update status
        try:
            error_update = {
                "jobId": jobId,
                "status": "failed",
                "error": user_error
            }
            response = requests.post(
                f"{API_UPDATE_URL.replace('/update_status', '')}/update_error",
                json=error_update,
                timeout=5
            )
            
            if response.status_code == 404:
                from helpers import release_lock
                release_lock(sessionId)
        except Exception as api_err:
            print(f" Could not notify API about error: {api_err}")
            try:
              
                redis_client = redis.from_url(os.getenv("REDIS_URL"))
                redis_client.delete(f"session_lock:{sessionId}")
                print(f"🔓 Manually released lock for session: {sessionId}")
            except:
                pass
        
    finally:
        cleanup_job_files(jobId, img1_path, img2_path, result_path)

def callback(ch, method, properties, body):
    """RabbitMQ message callback"""
    try:
        job_data = json.loads(body)     
        process_job(job_data)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
      
        
    except Exception as e:
        import traceback
      
        traceback.print_exc()
        
        # Send to DLQ - don't requeue to avoid infinite loops
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    """Main worker loop"""

    
    # Verify Google Drive connection
    try:
    
        from google_drive_oauth import drive_service, GOOGLE_DRIVE_FOLDER_ID
        
        if drive_service is None:
            print(" Google Drive not authorized yet")
            print(" Visit http://localhost:8000/authorize to login")
            print(" Worker will use fallback local storage")
        else:
            print(f" Google Drive connected (OAuth)")
            print(f" Folder ID: {GOOGLE_DRIVE_FOLDER_ID or 'Root (My Drive)'}")
    except Exception as e:
        print(f"❌ Google Drive error: {e}")
        print("🔄 Worker will use fallback local storage")
    
    # Connect to RabbitMQ
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        
        # Declare queue with TTL and DLX matching definitions.json
        queue_args = {
            'x-message-ttl': 300000,
            'x-dead-letter-exchange': 'dlx_face_swap'
        }
        channel.queue_declare(
            queue="face_swap_jobs", 
            durable=True,
            arguments=queue_args
        )
        
        # Set QoS - process one message at a time
        channel.basic_qos(prefetch_count=1)
        
        channel.basic_consume(
            queue="face_swap_jobs",
            on_message_callback=callback,
            auto_ack=False
        )
        
        channel.start_consuming()
        
    except KeyboardInterrupt:
        print("\n🛑 Worker stopped by user")
        if 'channel' in locals():
            channel.stop_consuming()
        if 'connection' in locals():
            connection.close()
        client.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import sys
        sys.exit(1)