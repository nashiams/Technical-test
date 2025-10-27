"use client";

import { useEffect } from "react";
import { useFaceSwapStore } from "@/store/faceSwapStore";
import UploadSection from "@/components/molecules/UploadSection";
import ResultSection from "@/components/molecules/ResultSection";
import { publishFaceSwap, checkStatus } from "@/lib/api";

export default function FaceSwapClient() {
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
        } else if (response.status === "failed") {
          setStatus("error");
          setError("Please try different photos.");
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
    <div className="space-y-12">
      {/* Upload Section with more spacing */}
      <UploadSection
        image1={image1}
        image2={image2}
        onImage1Change={setImage1}
        onImage2Change={setImage2}
      />

      {/* Action Button with more spacing */}
      <div className="flex justify-center pt-4">
        <button
          onClick={handleSwap}
          disabled={!canProcess}
          className="px-12 py-4 text-lg font-semibold rounded-lg transition-all transform hover:scale-105 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50 shadow-lg"
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

      {/* Result Section with more spacing */}
      <ResultSection status={status} resultUrl={resultUrl} error={error} />

      {/* Reset Button */}
      {status !== "idle" && (
        <div className="flex justify-center pt-8">
          <button
            onClick={reset}
            className="px-8 py-3 rounded-lg transition-colors hover:bg-opacity-80"
            style={{
              border: `2px solid var(--color-border)`,
              color: "var(--color-foreground)",
              fontFamily: "var(--font-body)",
            }}
          >
            Start Over
          </button>
        </div>
      )}
    </div>
  );
}
