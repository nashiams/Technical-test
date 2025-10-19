"use client";

import { useEffect } from "react";
import { useFaceSwapStore } from "@/store/faceSwapStore";
import Navbar from "@/components/molecules/Navbar";
import UploadSection from "@/components/molecules/UploadSection";
import { checkStatus, publishFaceSwap } from "@/lib/api";
import ResultSection from "@/components/molecules/ResultSection";

export default function Home() {
  const {
    image1,
    image2,
    jobId,
    status,
    resultUrl,
    error,
    setImage1,
    setImage2,
    setJobId,
    setStatus,
    setResultUrl,
    setError,
    reset,
  } = useFaceSwapStore();

  const canProcess = image1 && image2 && status === "idle";

  const handleSwap = async () => {
    if (!image1 || !image2) return;

    try {
      setStatus("uploading");
      setError(null);

      const response = await publishFaceSwap(image1, image2);
      setJobId(response.jobId);
      setStatus("processing");
    } catch (err) {
      setStatus("error");
      setError(
        err instanceof Error ? err.message : "Failed to start face swap"
      );
    }
  };

  useEffect(() => {
    if (status !== "processing" || !jobId) return;

    const pollStatus = async () => {
      try {
        const response = await checkStatus(jobId);

        if (response.status === "completed" && response.image_url) {
          setResultUrl(response.image_url);
          setStatus("completed");
        } else if (response.status === "processing") {
          // Continue polling
        } else {
          setStatus("error");
          setError("Unexpected status: " + response.status);
        }
      } catch (err) {
        setStatus("error");
        setError(err instanceof Error ? err.message : "Failed to check status");
      }
    };

    const interval = setInterval(pollStatus, 2000);
    pollStatus(); // Initial call

    return () => clearInterval(interval);
  }, [status, jobId, setStatus, setResultUrl, setError]);

  return (
    <div className="h-screen flex flex-col ">
      <Navbar />
      <main className="flex-1 flex flex-col ">
        <div className="flex-1 flex flex-col max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-4">
          {/* Compact Header */}
          <div className="text-center mb-6">
            <h1
              className="hero-title text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight mb-3"
              style={{
                color: "var(--color-foreground)",
              }}
            >
              Free Unlimited Face Swapper
            </h1>
            <p
              className="text-sm sm:text-base max-w-3xl mx-auto"
              style={{
                fontFamily: "var(--font-body)",
                color: "var(--color-secondary-text)",
              }}
            >
              Free Face Swap is your go-to online tool for quick, effortless
              face swaps. No logins, no tokens, no subscriptions, no filters.
              Just upload your photos, hit swap, and get instant results in
              seconds. We use best ML model in the market. All are 100% FREE,
              and your data is automatically deleted when done.
            </p>
          </div>

          {/* Upload Section - Compact */}
          <div className="flex-1 min-h-0">
            <UploadSection
              image1={image1}
              image2={image2}
              onImage1Change={setImage1}
              onImage2Change={setImage2}
            />
          </div>

          {/* Action Button */}
          <div className="flex justify-center py-4">
            <button
              onClick={handleSwap}
              disabled={!canProcess}
              className="px-8 py-3 font-semibold rounded-lg transition-all transform hover:scale-105 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
              style={{
                backgroundColor: canProcess
                  ? "var(--color-primary)"
                  : "var(--color-input-bg)",
                color: "var(--color-foreground)",
                fontFamily: "var(--font-body)",
              }}
            >
              Swap Faces
            </button>
          </div>

          {/* Result Section */}
          {status !== "idle" && (
            <ResultSection
              status={status}
              resultUrl={resultUrl}
              error={error}
            />
          )}

          {/* Reset Button */}
          {status !== "idle" && (
            <div className="flex justify-center py-3">
              <button
                onClick={reset}
                className="px-6 py-2 rounded-lg transition-colors text-sm"
                style={{
                  border: `1px solid var(--color-border)`,
                  color: "var(--color-foreground)",
                  fontFamily: "var(--font-body)",
                }}
              >
                Start Over
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
