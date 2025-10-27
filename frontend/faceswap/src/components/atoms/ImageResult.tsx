"use client";

import { useState, useCallback } from "react";
import { Download, ImageIcon, AlertCircle } from "lucide-react";
import Loader from "@/components/atoms/Loader";

interface ImageResultProps {
  status: "idle" | "uploading" | "processing" | "completed" | "error";
  resultUrl: string | null;
  error: string | null;
  label: string;
}

export default function ImageResult({
  status,
  resultUrl,
  error,
  label,
}: ImageResultProps) {
  const [imageLoaded, setImageLoaded] = useState(false);

  // Convert Google Drive URL to thumbnail format
  const getImageUrl = useCallback((url: string | null) => {
    if (!url) return null;

    const fileIdMatch = url.match(/[?&]id=([^&]+)/);
    if (fileIdMatch) {
      const fileId = fileIdMatch[1];
      return `https://drive.google.com/thumbnail?id=${fileId}&sz=w2000`;
    }

    return url;
  }, []);

  const displayUrl = getImageUrl(resultUrl);

  const handleImageLoad = useCallback(() => {
    setImageLoaded(true);
  }, []);

  const handleDownload = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      if (resultUrl) {
        const link = document.createElement("a");
        link.href = resultUrl;
        link.download = "face-swap-result.jpg";
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    },
    [resultUrl]
  );

  return (
    <div
      className="relative border-2 border-dashed rounded-xl transition-all duration-300 group flex items-center justify-center"
      style={{
        borderColor: "var(--color-border)",
        backgroundColor: "var(--color-input-bg)",
        minHeight: "250px",
        height: "100%",
      }}
    >
      {status === "idle" && (
        <div
          className="flex flex-col items-center justify-center p-6"
          style={{ color: "var(--color-secondary-text)" }}
        >
          <ImageIcon className="w-12 h-12 mb-4" />
          <p className="text-base font-semibold mb-2">{label}</p>
          <p className="text-sm">Waiting for process to start</p>
        </div>
      )}

      {(status === "uploading" || status === "processing") && (
        <div className="text-center space-y-4 p-6">
          <Loader />
          <div>
            <p
              className="text-base font-semibold mb-2"
              style={{ color: "var(--color-foreground)" }}
            >
              {status === "uploading" ? "Uploading..." : "Processing..."}
            </p>
            <p
              className="text-sm"
              style={{ color: "var(--color-secondary-text)" }}
            >
              {label}
            </p>
          </div>
        </div>
      )}

      {status === "completed" && displayUrl && (
        <div className="relative w-full h-full flex items-center justify-center p-4">
          <img
            src={displayUrl}
            alt={label}
            className="max-w-full max-h-full object-contain rounded-lg"
            style={{
              opacity: imageLoaded ? 1 : 0,
              transition: "opacity 0.3s ease-in-out",
            }}
            onLoad={handleImageLoad}
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
          {!imageLoaded && (
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader />
            </div>
          )}
          <button
            onClick={handleDownload}
            className="absolute top-2 right-2 p-2 rounded-full transition-all hover:scale-110 shadow-lg z-20"
            style={{
              backgroundColor: "var(--color-primary)",
              color: "var(--color-foreground)",
            }}
            aria-label="Download image"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      )}

      {status === "error" && (
        <div className="text-center space-y-4 p-6">
          <AlertCircle
            className="w-12 h-12 mx-auto"
            style={{ color: "var(--color-error)" }}
          />
          <div>
            <p
              className="text-base font-semibold mb-2"
              style={{ color: "var(--color-error)" }}
            >
              Error occurred
            </p>
            <p
              className="text-sm"
              style={{ color: "var(--color-secondary-text)" }}
            >
              {error || "Failed to process image"}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
