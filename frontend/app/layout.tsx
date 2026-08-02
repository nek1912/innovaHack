import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { ClientProviders } from "@/components/ClientProviders";

export const metadata: Metadata = {
  title: "AgentFinance Control System",
  description: "Mission control for autonomous financial agents",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full bg-background text-foreground">
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        <Sidebar />
        <div className="md:ml-60 min-h-screen">
          <main id="main-content" className="p-4 md:p-6 pt-16 md:pt-6">
            <ClientProviders>{children}</ClientProviders>
          </main>
        </div>
      </body>
    </html>
  );
}
