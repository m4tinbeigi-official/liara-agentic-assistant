import type { Metadata, Viewport } from "next";
import "./globals.css";

export const viewport: Viewport = {
  themeColor: "#0f172a",
};

export const metadata: Metadata = {
  title: "Liara Agentic Copilot | دستیار هوشمند لیارا",
  description:
    "دستیار هوشمند استقرار و مستندات پلتفرم ابری لیارا — تحلیل خطا، ساخت کانفیگ و راهنمای فارسی",
  icons: { icon: "/favicon.ico" },
  openGraph: {
    title: "Liara Agentic Copilot",
    description: "دستیار هوشمند عاملی پلتفرم ابری لیارا",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fa" dir="rtl" className="h-full">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col bg-slate-950 antialiased font-vazir">
        {children}
      </body>
    </html>
  );
}
