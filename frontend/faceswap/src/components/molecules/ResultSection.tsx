"use client";

import Loader from "@/components/atoms/Loader";

interface ResultSectionProps {
  status: "idle" | "uploading" | "processing" | "completed" | "error";
  resultUrl: string | null;
  error: string | null;
}

export default function ResultSection({
  status,
  resultUrl,
  error,
}: ResultSectionProps) {
  if (status === "idle") return null;

  // Convert Google Drive URL to thumbnail format
  const getImageUrl = (url: string | null) => {
    if (!url) return null;

    const fileIdMatch = url.match(/[?&]id=([^&]+)/);
    if (fileIdMatch) {
      const fileId = fileIdMatch[1];
      return `https://drive.google.com/thumbnail?id=${fileId}&sz=w1200`;
    }

    return url;
  };

  const displayUrl = getImageUrl(resultUrl);

  return (
    <div className="w-full max-w-2xl mx-auto mt-6">
      <h2
        className="text-xl font-bold text-center mb-4"
        style={{
          fontFamily: "var(--font-heading)",
          color: "var(--color-foreground)",
        }}
      >
        Result
      </h2>

      <div
        className="border-2 rounded-xl p-6 flex items-center justify-center"
        style={{
          borderColor: "var(--color-border)",
          backgroundColor: "var(--color-input-bg)",
          minHeight: "300px",
          maxHeight: "500px",
        }}
      >
        {(status === "uploading" || status === "processing") && (
          <div className="text-center space-y-4">
            <Loader />
            <div>
              <p
                className="text-base font-medium mb-2"
                style={{ color: "var(--color-foreground)" }}
              >
                {status === "uploading"
                  ? "Uploading images..."
                  : "Processing face swap..."}
              </p>
              <p
                className="text-sm"
                style={{ color: "var(--color-secondary-text)" }}
              >
                This may take a few seconds
              </p>
            </div>
          </div>
        )}

        {status === "completed" && displayUrl && (
          <div className="w-full flex flex-col items-center justify-center gap-4">
            {/* Image container with constrained size */}
            <div
              className="w-full flex items-center justify-center overflow-hidden rounded-lg"
              style={{ maxHeight: "400px" }}
            >
              <img
                src={displayUrl}
                alt="Face swap result"
                className="max-w-full max-h-full object-contain"
                style={{
                  maxWidth: "100%",
                  maxHeight: "400px",
                  width: "auto",
                  height: "auto",
                  border: `1px solid var(--color-border)`,
                }}
                onError={(e) => {
                  console.error("Failed to load image:", displayUrl);
                  const target = e.target as HTMLImageElement;
                  if (!target.src.includes("/proxy-image")) {
                    target.src = `/api/proxy-image?url=${encodeURIComponent(
                      resultUrl || ""
                    )}`;
                  }
                }}
              />
            </div>

            {/* Download button */}
            <a
              href={resultUrl || "#"}
              download="face-swap-result.jpg"
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-2.5 rounded-lg text-sm font-semibold transition-all hover:scale-105 active:scale-95"
              style={{
                backgroundColor: "var(--color-primary)",
                color: "var(--color-foreground)",
                fontFamily: "var(--font-body)",
              }}
            >
              Download Result
            </a>
          </div>
        )}

        {status === "error" && (
          <div className="text-center space-y-3">
            <p
              className="font-semibold text-base"
              style={{ color: "var(--color-error)" }}
            >
              Error occurred
            </p>
            <p
              className="text-sm"
              style={{ color: "var(--color-secondary-text)" }}
            >
              {error || "Something went wrong"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
