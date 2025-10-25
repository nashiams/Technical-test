# server.py
import datetime
from flask import Flask, request, jsonify, send_file
import uuid
import os
from helpers import publish_job, acquire_lock, release_lock
from db import jobs_collection  
from oauth_routes import register_oauth_routes

app = Flask(__name__)

# Disable response caching globally
@app.after_request
def add_no_cache_headers(response):
    """Add no-cache headers to all responses"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Register OAuth routes
register_oauth_routes(app)

@app.route("/health", methods=["GET"])
def health():
    """ Health check endpoint."""

    random_value = os.urandom(8).hex()

    return jsonify({"status": "ok", "service": "flask-api", "random": random_value}), 200


@app.route("/publish", methods=["POST"])
def publish():
    """
     Receive two images + sessionId (multipart/form-data).
    - Enforce one active job per session (via Redis/Redlock).
    - Save files safely to /tmp/<job_id>/...
    - Create job record in MongoDB.
    - Publish job to RabbitMQ for processing.
    Returns: { "status": "processing", "jobId": "<uuid>" }
    """

    session_id = request.form.get("sessionId")
    if not session_id:
        return jsonify({"error": "Missing sessionId"}), 400

    #  Acquire lock (one active job per session)
    lock = acquire_lock(session_id)
    if not lock:
        return jsonify({"error": "Previous job still processing"}), 429

    if "image1" not in request.files or "image2" not in request.files:
        release_lock(session_id)
        return jsonify({"error": "Missing image1 or image2"}), 400

    #  Generate jobId + create job directory
    job_id = str(uuid.uuid4())
    print(f"🆕 Generated NEW job_id: {job_id} for session: {session_id}")
    
    job_dir = f"/tmp/{job_id}"
    try:
        os.makedirs(job_dir, exist_ok=True)
    except Exception as e:
        release_lock(session_id)
        return jsonify({"error": f"Failed to create job dir: {e}"}), 500

    # Save images with unique names to avoid filename conflicts
    try:
        img1 = request.files["image1"]
        img2 = request.files["image2"]

        ext1 = os.path.splitext(img1.filename)[1] or ".jpg"
        ext2 = os.path.splitext(img2.filename)[1] or ".jpg"

        unique1 = f"image1_{uuid.uuid4().hex}{ext1}"
        unique2 = f"image2_{uuid.uuid4().hex}{ext2}"

        img1_path = os.path.join(job_dir, unique1)
        img2_path = os.path.join(job_dir, unique2)

        img1.save(img1_path)
        img2.save(img2_path)
    except Exception as e:
        release_lock(session_id)
        return jsonify({"error": f"Failed to save files: {e}"}), 500

    #  Create MongoDB record
    try:
        from datetime import datetime
        now = datetime.utcnow()

        jobs_collection.insert_one({
            "sessionId": session_id,
            "jobId": job_id,
            "status": "processing",  # frontend expects "processing" or "completed"
            "resultUrl": None,
            "createdAt": now,
            "updatedAt": now
        })
    except Exception as e:
        release_lock(session_id)
        return jsonify({"error": f"DB error: {e}"}), 500

    #  Publish to RabbitMQ (worker will process)
    try:
        publish_job(
            job_id=job_id,
            img1_path=img1_path,
            img2_path=img2_path,
            session_id=session_id
        )
    except Exception as e:
        jobs_collection.update_one(
            {"jobId": job_id},
            {"$set": {"status": "error", "updatedAt": datetime.utcnow()}}
        )
        release_lock(session_id)
        return jsonify({"error": f"Failed to publish job: {e}"}), 500

    
    # Create response with explicit no-cache headers
    response = jsonify({"status": "processing", "jobId": job_id})
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response, 200


@app.route("/status/<job_id>", methods=["GET"])
def status(job_id):

    """
    Return job status from MongoDB in the exact shape frontend expects:
    - { "status": "processing" }
    - or { "status": "completed", "image_url": "<url>" }
    - or { "status": "not_found" }
    """

    job = jobs_collection.find_one({"jobId": job_id}, {"_id": 0})
    if not job:
        return jsonify({"status": "not_found"}), 404

    if job.get("status") == "completed":
        return jsonify({"status": "completed", "image_url": job.get("resultUrl")}), 200
    elif job.get("status") == "failed":
        return jsonify({"status": "failed", "error": job.get("error")}), 200
    else:
        return jsonify({"status": "processing"}), 200


@app.route("/update_status", methods=["POST"])
def update_status():
    """
    INTERNAL endpoint used by the worker to report completion.
    """
    data = request.get_json(force=True)
    job_id = data.get("jobId")
    result_url = data.get("resultUrl")


    if not job_id or not result_url:
        return jsonify({"error": "Missing jobId or resultUrl"}), 400

    job = jobs_collection.find_one({"jobId": job_id})
    if not job:
        return jsonify({"error": "Job not found"}), 404

    session_id = job.get("sessionId")

    jobs_collection.update_one(
        {"jobId": job_id},
        {"$set": {"status": "completed", "resultUrl": result_url}}
    )

    # Release session lock (worker finished)
    try:
        release_lock(session_id)
    except Exception as e:
        print(f" Failed to release lock: {e}")

    return jsonify({"status": "updated"}), 200


@app.route("/update_error", methods=["POST"])
def update_error():
    """
    INTERNAL endpoint to handle job failures from worker
    """
    data = request.get_json(force=True)
    job_id = data.get("jobId")
    error = data.get("error")
    
    
    if not job_id:
        return jsonify({"error": "Missing jobId"}), 400
    
    job = jobs_collection.find_one({"jobId": job_id})
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    session_id = job.get("sessionId")
    
    # Update job status to failed
    jobs_collection.update_one(
        {"jobId": job_id},
        {"$set": {
            "status": "failed",
            "error": error or "Processing failed",
            "updatedAt": datetime.utcnow()
        }}
    )
    
    # Release session lock
    try:
        release_lock(session_id)
    except Exception as e:
        print(f"❌ Failed to release lock: {e}")
    
    return jsonify({"status": "updated"}), 200


@app.route("/results/<filename>", methods=["GET"])
def serve_result(filename):
    """Serve result images (fallback if Firebase is unavailable)"""
    try:
        file_path = f"/tmp/results/{filename}"
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        return send_file(file_path, mimetype="image/jpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 5000))
    app.run(host="0.0.0.0", port=port)
