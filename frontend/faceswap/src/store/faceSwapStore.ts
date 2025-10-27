import { create } from "zustand";

interface FaceSwapState {
  image1: File | null;
  image2: File | null;
  jobId: string | null;
  status: "idle" | "uploading" | "processing" | "completed" | "error";
  resultUrl: string | null;
  error: string | null;
  setImage1: (file: File | null) => void;
  setImage2: (file: File | null) => void;
  setJobId: (id: string) => void;
  setStatus: (status: FaceSwapState["status"]) => void;
  setResultUrl: (url: string) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useFaceSwapStore = create<FaceSwapState>((set) => ({
  image1: null,
  image2: null,
  jobId: null,
  status: "idle",
  resultUrl: null,
  error: null,
  setImage1: (file) => set({ image1: file }),
  setImage2: (file) => set({ image2: file }),
  setJobId: (id) =>
    set({
      jobId: id,
      // Clear old result when setting new jobId
      resultUrl: null,
      error: null,
    }),
  setStatus: (status) => set({ status }),
  setResultUrl: (url) => set({ resultUrl: url }),
  setError: (error) => set({ error }),
  reset: () =>
    set({
      image1: null,
      image2: null,
      jobId: null,
      status: "idle",
      resultUrl: null,
      error: null,
    }),
}));
