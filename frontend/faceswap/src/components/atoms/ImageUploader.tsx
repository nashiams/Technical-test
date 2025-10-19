"use client";

import { useCallback } from "react";
import { Upload, X } from "lucide-react";

interface ImageUploaderProps {
  onFileSelect: (file: File | null) => void;
  preview: string | null;
  label: string;
}

export default function ImageUploader({
  onFileSelect,
  preview,
  label,
}: ImageUploaderProps) {
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith("image/")) {
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
  };

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    onFileSelect(null);
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      className="relative border-2 border-dashed rounded-xl hover:border-primary transition-all duration-300 cursor-pointer group flex items-center justify-center"
      style={{
        borderColor: "var(--color-border)",
        backgroundColor: "var(--color-input-bg)",
        minHeight: "250px",
        height: "100%",
      }}
    >
      <input
        type="file"
        accept="image/*"
        onChange={handleChange}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
      />
      {preview ? (
        <div className="relative w-full h-full flex items-center justify-center p-4">
          <img
            src={preview}
            alt={label}
            className="max-w-full max-h-full object-contain rounded-lg"
          />
          <button
            onClick={handleRemove}
            className="absolute top-2 right-2 p-2 rounded-full transition-all hover:scale-110 shadow-lg z-20"
            style={{
              backgroundColor: "var(--color-error)",
              color: "var(--color-foreground)",
            }}
            aria-label="Remove image"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ) : (
        <div
          className="flex flex-col items-center justify-center group-hover:scale-105 transition-transform duration-300 p-6"
          style={{ color: "var(--color-secondary-text)" }}
        >
          <Upload className="w-12 h-12 mb-4" />
          <p className="text-base font-semibold mb-2">{label}</p>
          <p className="text-sm">Drag & drop or click</p>
          <p className="text-xs mt-2 opacity-70">JPG, PNG, WEBP</p>
        </div>
      )}
    </div>
  );
}
