import type { Metadata, Viewport } from "next";
import { Vazirmatn } from "next/font/google";
import "./globals.css";

const vazirmatn = Vazirmatn({
  subsets: ["arabic", "latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-vazirmatn",
  display: "swap",
});

export const viewport: Viewport = {
  themeColor: "#0f172a",
};

export const metadata: Metadata = {
  title: "Liara Agentic Copilot | دستیار هوشمند لیارا",
  description:
    "دستیار هوشمند لیارا برای استقرار، عیب‌یابی و مستندات — تحلیل آنی خطاها، ساخت کانفیگ و Dockerfile و پاسخ به سوالات فنی، همه به فارسی روان.",
  icons: { icon: "/favicon.ico" },
  openGraph: {
    title: "Liara Agentic Copilot",
    description:
      "دستیار هوشمند عامل‌محور پلتفرم ابری لیارا؛ همراه شما در استقرار، رفع خطا و ساخت کانفیگ.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fa" dir="rtl" className={`h-full ${vazirmatn.variable}`}>
      <body className="min-h-full flex flex-col bg-slate-950 antialiased font-vazir">
        {children}
      </body>
    </html>
  );
}
