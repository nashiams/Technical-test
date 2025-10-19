import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { v4 as uuidv4 } from "uuid";

const BACKEND_API_URL = process.env.BACKEND_API_URL || "http://localhost:8000";
const SESSION_COOKIE_NAME = "face_swap_sessionId";

export async function POST(request: NextRequest) {
  try {
    // Get or create sessionId
    const cookieStore = await cookies();
    let sessionId = cookieStore.get(SESSION_COOKIE_NAME)?.value;

    if (!sessionId) {
      // Generate new session ID
      sessionId = uuidv4();
      console.log(`🆕 New session created: ${sessionId}`);
    } else {
      console.log(`♻️ Using existing session: ${sessionId}`);
    }

    // Get form data from request
    const formData = await request.formData();
    const image1 = formData.get("image1");
    const image2 = formData.get("image2");

    if (!image1 || !image2) {
      return NextResponse.json(
        { error: "Both images are required" },
        { status: 400 }
      );
    }

    // Forward request to Python backend
    const backendFormData = new FormData();
    backendFormData.append("image1", image1);
    backendFormData.append("image2", image2);
    backendFormData.append("sessionId", sessionId);

    console.log(`📤 Forwarding to backend: ${BACKEND_API_URL}/publish`);

    const backendResponse = await fetch(`${BACKEND_API_URL}/publish`, {
      method: "POST",
      body: backendFormData,
    });

    if (!backendResponse.ok) {
      const error = await backendResponse.json();
      return NextResponse.json(
        { error: error.error || "Backend processing failed" },
        { status: backendResponse.status }
      );
    }

    const data = await backendResponse.json();

    // Create response with session cookie
    const response = NextResponse.json(data, { status: 200 });

    // Set session cookie (expires in 1 hour)
    response.cookies.set({
      name: SESSION_COOKIE_NAME,
      value: sessionId,
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60, // 1 hour
      path: "/",
    });

    console.log(`✅ Job created: ${data.jobId}`);

    return response;
  } catch (error) {
    console.error("❌ Publish API error:", error);
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : "Internal server error",
      },
      { status: 500 }
    );
  }
}
