import json
import os
import uuid
import pika
import redis
from db import jobs_collection

# ================== REDIS (Upstash) SETUP ==================
REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# ================== RABBITMQ SETUP ==================
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_DEFAULT_USER", "appuser")
RABBITMQ_PASS = os.getenv("RABBITMQ_DEFAULT_PASS", "changeme123")

# Build RabbitMQ URL without vhost (uses default '/')
RABBITMQ_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}"

# ================== HELPER: Publish to RabbitMQ ==================
def publish_job(job_id, img1_path, img2_path, session_id):
    """
    Publish a face swap job to RabbitMQ queue.
    """
    try:
        # Connect to RabbitMQ
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        
        # Ensure queue exists with same args as definitions.json
        queue_args = {
            'x-message-ttl': 300000,  # 5 minutes
            'x-dead-letter-exchange': 'dlx_face_swap'  # Failed messages
        }
        channel.queue_declare(
            queue="face_swap_jobs", 
            durable=True,
            arguments=queue_args
        )
        
        # Prepare message - use consistent field names
        message = {
            "jobId": job_id,
            "img1_path": img1_path,
            "img2_path": img2_path,
            "sessionId": session_id
        }
        
        print(f"📤 Publishing job {job_id}: {json.dumps(message, indent=2)}")
        
        # Publish message with persistent delivery
        channel.basic_publish(
            exchange="",  # Default exchange (direct to queue)
            routing_key="face_swap_jobs",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type="application/json",
                expiration="300000"  # Match TTL (5 minutes in ms)
            )
        )
        
        
        # Close connection
        connection.close()
        
    except Exception as e:
        print(f"❌ Failed to publish job {job_id}: {e}")
        raise e


# ================== HELPER: Redis Lock (1 job per session) ==================
def acquire_lock(session_id, timeout=300):
    """Try to acquire a Redis lock so only one active job per session."""
    try:
        # Simple SET NX (set if not exists) with expiration
        lock_key = f"session_lock:{session_id}"
        
        # Try to set the key (returns True if set, False if already exists)
        locked = redis_client.set(lock_key, "locked", nx=True, ex=timeout)
        
        if locked:
            return True
        else:
            return False
    except Exception as e:
        return False


def release_lock(session_id):
    """Release the Redis lock by deleting the key."""
    try:
        lock_key = f"session_lock:{session_id}"
        
        # Check if key exists before deletion
        exists_before = redis_client.exists(lock_key)
        print(f" Lock key '{lock_key}' exists before deletion: {exists_before}")
        
        # Delete the key
        result = redis_client.delete(lock_key)
        
        # Verify deletion
        exists_after = redis_client.exists(lock_key)
        
        if result > 0:
            if exists_after:
                print(f" WARNING: Key still exists after deletion!")
        else:
            print(f" No lock found to release for session: {session_id} (key: {lock_key})")
            
    except Exception as e:
        import traceback
        traceback.print_exc()

# ================== HELPER: Job Creation ==================
def create_job(session_id):
    """Insert a new job document into MongoDB."""
    job_id = str(uuid.uuid4())
    job_doc = {
        "jobId": job_id,
        "sessionId": session_id,
        "status": "queued",
        "resultUrl": None
    }
    jobs_collection.insert_one(job_doc)
    return job_id

# ================== HELPER: Job Status ==================
def update_job_status(job_id, status, result_url=None):
    """Update job status in MongoDB."""
    update_data = {"status": status}
    if result_url:
        update_data["resultUrl"] = result_url
    jobs_collection.update_one({"jobId": job_id}, {"$set": update_data})
