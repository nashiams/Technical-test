"use client";

import { useState, useEffect } from "react";
import ImageUploader from "@/components/atoms/ImageUploader";

interface UploadSectionProps {
  image1: File | null;
  image2: File | null;
  onImage1Change: (file: File) => void;
  onImage2Change: (file: File) => void;
}

export default function UploadSection({
  image1,
  image2,
  onImage1Change,
  onImage2Change,
}: UploadSectionProps) {
  const [preview1, setPreview1] = useState<string | null>(null);
  const [preview2, setPreview2] = useState<string | null>(null);

  useEffect(() => {
    if (image1) {
      const url = URL.createObjectURL(image1);
      setPreview1(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setPreview1(null);
    }
  }, [image1]);

  useEffect(() => {
    if (image2) {
      const url = URL.createObjectURL(image2);
      setPreview2(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setPreview2(null);
    }
  }, [image2]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full h-full min-h-0">
      <ImageUploader
        onFileSelect={onImage1Change}
        preview={preview1}
        label="Upload Face Image"
      />
      <ImageUploader
        onFileSelect={onImage2Change}
        preview={preview2}
        label="Upload Target Image"
      />
    </div>
  );
}
