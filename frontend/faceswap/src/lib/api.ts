interface PublishResponse {
  jobId: string;
  status: string;
  error?: string;
}

interface StatusResponse {
  status: string;
  image_url?: string;
  error?: string;
}

/**
 * Submit images for face swap processing
 * This hits the Next.js API route which handles session management
 */
export async function publishFaceSwap(
  image1: File,
  image2: File
): Promise<PublishResponse> {
  const formData = new FormData();
  formData.append("image1", image1);
  formData.append("image2", image2);

  const response = await fetch("/api/publish", {
    method: "POST",
    body: formData,
    credentials: "include",
    // Prevent caching
    cache: "no-store",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "Failed to publish face swap");
  }

  const data = await response.json();

  return data;
}

/**
 * Check the status of a face swap job
 * Used for polling until job is completed
 */
export async function checkStatus(jobId: string): Promise<StatusResponse> {
  const response = await fetch(
    `/api/status?jobId=${encodeURIComponent(jobId)}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      // Disable caching for polling
      cache: "no-store",
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "Failed to check status");
  }

  return response.json();
}
