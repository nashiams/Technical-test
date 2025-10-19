import { NextRequest, NextResponse } from "next/server";

const BACKEND_API_URL = process.env.BACKEND_API_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  try {
    // Get jobId from query parameters
    const { searchParams } = new URL(request.url);
    const jobId = searchParams.get("jobId");

    if (!jobId) {
      return NextResponse.json({ error: "jobId is required" }, { status: 400 });
    }

    console.log(`🔍 Checking status for job: ${jobId}`);

    // Forward request to Python backend
    const backendResponse = await fetch(`${BACKEND_API_URL}/status/${jobId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      // Disable caching for polling
      cache: "no-store",
    });

    if (!backendResponse.ok) {
      const error = await backendResponse.json();
      return NextResponse.json(
        { error: error.error || "Failed to check status" },
        { status: backendResponse.status }
      );
    }

    const data = await backendResponse.json();

    // Add no-cache headers for polling
    const response = NextResponse.json(data, { status: 200 });
    response.headers.set(
      "Cache-Control",
      "no-store, no-cache, must-revalidate"
    );
    response.headers.set("Pragma", "no-cache");
    response.headers.set("Expires", "0");

    if (data.status === "completed") {
      console.log(`✅ Job ${jobId} completed`);
    } else {
      console.log(`⏳ Job ${jobId} still ${data.status}`);
    }

    return response;
  } catch (error) {
    console.error("❌ Status API error:", error);
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : "Internal server error",
      },
      { status: 500 }
    );
  }
}
