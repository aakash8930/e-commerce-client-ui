import type { Metadata } from "next";
import "./globals.css";
import StoreHydrator from "@/components/StoreHydrator";
import { ToastContainer } from "react-toastify";

export const metadata: Metadata = {
  title: "Slotly — Get booked without the back-and-forth",
  description:
    "Slotly gives service businesses a booking page, smart availability, and automated reminders. Share your link and let clients book you 24/7.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white text-slate-900 antialiased">
        <StoreHydrator />
        {children}
        <ToastContainer position="bottom-right" />
      </body>
    </html>
  );
}
