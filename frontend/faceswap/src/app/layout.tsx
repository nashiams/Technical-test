import type { Metadata } from "next";
import { Playfair_Display, Source_Sans_3, Inter_Tight } from "next/font/google";
import "./globals.css";

import ErrorReporter from "@/components/ErrorReporter";
import Script from "next/script";

const playfairDisplay = Playfair_Display({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-heading",
});

const sourceSans3 = Source_Sans_3({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-body",
});

const interTight = Inter_Tight({
  subsets: ["latin"],
  weight: ["700"],
  variable: "--font-hero",
});

export const metadata: Metadata = {
  title: "Free Face Swap - Swap Faces Freely Online",
  description:
    "Upload two images and let Free Face Swap swap the faces seamlessly",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${playfairDisplay.variable} ${sourceSans3.variable} ${interTight.variable} antialiased`}
      >
        <ErrorReporter />
        <Script
          src="https://slelguoygbfzlpylpxfs.supabase.co/storage/v1/object/public/scripts//route-messenger.js"
          strategy="afterInteractive"
          data-target-origin="*"
          data-message-type="ROUTE_CHANGE"
          data-include-search-params="true"
          data-only-in-iframe="true"
          data-debug="true"
          data-custom-data='{"appName": "YourApp", "version": "1.0.0", "greeting": "hi"}'
        />
        {children}
      </body>
    </html>
  );
}
