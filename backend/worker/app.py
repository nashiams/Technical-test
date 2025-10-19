import os
import json
import pika
import requests
from pymongo import MongoClient
from datetime import datetime

print("=" * 60)
print("🚀 Face Swap Worker Starting...")
print("=" * 60)

# Setup environment
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://appuser:changeme123@rabbitmq:5672")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
API_UPDATE_URL = os.getenv("API_UPDATE_URL", "http://api:5000/update_status")

print(f"📡 RabbitMQ URL: {RABBITMQ_URL}")
print(f"🗄️  MongoDB URI: {MONGO_URI[:50]}...")
print(f"🔄 API Update URL: {API_UPDATE_URL}")

# Connect MongoDB
try:
    print("\n🔌 Connecting to MongoDB...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Test connection
    client.server_info()
    db = client["face_swap"]
    jobs_collection = db["jobs"]
    print("✅ MongoDB connected successfully")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    raise e

# Initialize face swap model
try:
    print("\n🤖 Loading face swap models...")
    from face_swap import prepare_app, swap_faces
    app, swapper = prepare_app()
    print("✅ Face swap models loaded")
except Exception as e:
    print(f"❌ Failed to load face swap models: {e}")
    import traceback
    traceback.print_exc()
    raise e

# Import helpers after models are loaded
try:
    print("\n📦 Loading helpers...")
    from helpers import upload_to_google_drive, cleanup_job_files
    print("✅ Helpers loaded")
except Exception as e:
    print(f"❌ Failed to load helpers: {e}")
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
                print(f"⚠️ Failed to update job status via API: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Could not reach API to update status: {e}")
        
        print(f"✅ Job {jobId} completed successfully")
        
    except Exception as e:
        print(f"❌ Job {jobId} failed: {str(e)}")
        # Update MongoDB status to failed
        jobs_collection.update_one(
            {"jobId": jobId},
            {"$set": {
                "status": "failed",
                "error": str(e),
                "updatedAt": datetime.utcnow()
            }}
        )
        
        # Try to notify API about failure (to release lock)
        try:
            requests.post(
                f"{API_UPDATE_URL.replace('/update_status', '')}/release_lock",
                json={"sessionId": sessionId},
                timeout=5
            )
        except:
            pass
        
        raise e
    finally:
        # Cleanup temporary files
        cleanup_job_files(jobId, img1_path, img2_path, result_path)

def callback(ch, method, properties, body):
    """RabbitMQ message callback"""
    try:
        job_data = json.loads(body)
        jobId = job_data.get('jobId')
        print(f"\n{'='*60}")
        print(f"📩 Received job: {jobId}")
        print(f"📋 Job data: {json.dumps(job_data, indent=2)}")
        print(f"{'='*60}\n")
        
        process_job(job_data)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
        print(f"\n{'='*60}")
        print(f"✅ Job {jobId} acknowledged and removed from queue")
        print(f"{'='*60}\n")
        
    except Exception as e:
        import traceback
        print(f"\n{'='*60}")
        print(f"❌ Error processing job: {e}")
        print(f"Stack trace:")
        traceback.print_exc()
        print(f"{'='*60}\n")
        # Send to DLQ - don't requeue to avoid infinite loops
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    """Main worker loop"""
    print("\n" + "=" * 60)
    print("🚀 Starting main worker loop...")
    print("=" * 60)
    
    # Verify Google Drive connection
    try:
        print("\n☁️ Verifying Google Drive connection...")
        from google_drive_oauth import drive_service, GOOGLE_DRIVE_FOLDER_ID
        
        if drive_service is None:
            print("⚠️ Google Drive not authorized yet")
            print("💡 Visit http://localhost:8000/authorize to login")
            print("🔄 Worker will use fallback local storage")
        else:
            print(f"✅ Google Drive connected (OAuth)")
            print(f"📁 Folder ID: {GOOGLE_DRIVE_FOLDER_ID or 'Root (My Drive)'}")
    except Exception as e:
        print(f"❌ Google Drive error: {e}")
        print("🔄 Worker will use fallback local storage")
    
    # Connect to RabbitMQ
    try:
        print("\n🐰 Connecting to RabbitMQ...")
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        print("✅ RabbitMQ connected")
        
        # Declare queue with TTL and DLX matching definitions.json
        print("\n📋 Declaring queue...")
        queue_args = {
            'x-message-ttl': 300000,
            'x-dead-letter-exchange': 'dlx_face_swap'
        }
        channel.queue_declare(
            queue="face_swap_jobs", 
            durable=True,
            arguments=queue_args
        )
        print("✅ Queue declared: face_swap_jobs")
        
        # Set QoS - process one message at a time
        channel.basic_qos(prefetch_count=1)
        print("✅ QoS set: prefetch_count=1")
        
        print("\n" + "=" * 60)
        print("✅ Worker is ready! Waiting for jobs...")
        print("=" * 60 + "\n")
        
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
        print(f"\n❌ Fatal error in main loop: {e}")
        import traceback
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Worker failed to start: {e}")
        import sys
        sys.exit(1)