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
    } else {
      console.log(` Using existing session: ${sessionId}`);
    }

    // Get form data from request
    const formData = await request.formData();
    const image1 = formData.get("image1") as File | null;
    const image2 = formData.get("image2") as File | null;

    console.log(`📥 Received files:`, {
      image1: image1
        ? `${image1.name} (${image1.size} bytes, ${image1.type})`
        : "null",
      image2: image2
        ? `${image2.name} (${image2.size} bytes, ${image2.type})`
        : "null",
    });

    if (!image1 || !image2) {
      return NextResponse.json(
        { error: "Both images are required" },
        { status: 400 }
      );
    }

    // Create new FormData for backend with proper file handling
    const backendFormData = new FormData();

    // Convert Files to Blobs with correct filename and type
    const blob1 = new Blob([await image1.arrayBuffer()], { type: image1.type });
    const blob2 = new Blob([await image2.arrayBuffer()], { type: image2.type });

    backendFormData.append("image1", blob1, image1.name);
    backendFormData.append("image2", blob2, image2.name);
    backendFormData.append("sessionId", sessionId);

    console.log(` FormData being sent:`, {
      image1: `${image1.name} (${blob1.size} bytes)`,
      image2: `${image2.name} (${blob2.size} bytes)`,
      sessionId: sessionId,
    });

    const backendResponse = await fetch(`${BACKEND_API_URL}/publish`, {
      method: "POST",
      body: backendFormData,
      // Don't set Content-Type - let fetch set it with boundary
    });

    if (!backendResponse.ok) {
      const error = await backendResponse.json();
      console.error(`❌ Backend error:`, error);
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
