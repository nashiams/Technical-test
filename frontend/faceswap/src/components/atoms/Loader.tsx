"use client";

export default function Loader() {
  return (
    <div className="flex items-center justify-center">
      <div className="square-circle-loader">
        <style jsx>{`
          .square-circle-loader {
            width: 50px;
            aspect-ratio: 1;
            border-radius: 50%;
            background: radial-gradient(farthest-side, #6366f1 94%, #0000)
                top/8px 8px no-repeat,
              conic-gradient(#0000 30%, #6366f1);
            -webkit-mask: radial-gradient(
              farthest-side,
              #0000 calc(100% - 8px),
              #000 0
            );
            animation: spin 1s infinite linear;
          }
          @keyframes spin {
            100% {
              transform: rotate(1turn);
            }
          }
        `}</style>
      </div>
    </div>
  );
}
