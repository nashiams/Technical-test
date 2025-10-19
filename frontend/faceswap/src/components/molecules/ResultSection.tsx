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

  return (
    <div className="w-full mt-4">
      <h2 className="text-xl font-bold text-center mb-3">Result</h2>

      <div
        className="border-2 border-border rounded-xl p-6 bg-secondary/50 flex items-center justify-center"
        style={{ minHeight: "250px", maxHeight: "400px" }}
      >
        {(status === "uploading" || status === "processing") && (
          <div className="text-center space-y-4">
            <Loader />
            <p className="text-base text-muted-foreground">
              {status === "uploading"
                ? "Uploading images..."
                : "Processing face swap..."}
            </p>
            <p className="text-sm text-muted-foreground/70">
              This may take a few seconds
            </p>
          </div>
        )}

        {status === "completed" && resultUrl && (
          <div className="w-full h-full flex items-center justify-center">
            <img
              src={resultUrl}
              alt="Face swap result"
              className="max-w-full max-h-full object-contain rounded-xl shadow-2xl"
            />
          </div>
        )}

        {status === "error" && (
          <div className="text-center text-red-400 space-y-3">
            <p className="font-semibold text-base">Error occurred</p>
            <p className="text-sm">{error || "Something went wrong"}</p>
          </div>
        )}
      </div>
    </div>
  );
}
