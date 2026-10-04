"use client";

import Link from "next/link";
import { signOut } from "firebase/auth";
import { usePathname, useRouter } from "next/navigation";
import { auth } from "@/lib/firebase";
import { useAuth } from "./auth-provider";
import { LanguageToggle } from "./language-toggle";
import { useLanguage } from "./language-provider";

const nav = [
  ["/dashboard", "Tổng quan", "Dashboard"],
  ["/learn", "Học", "Learn"],
  ["/practice", "Luyện tập", "Practice"],
  ["/progress", "Tiến trình", "Progress"],
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { devMode } = useAuth();
  const { language } = useLanguage();

  const logout = async () => {
    if (!devMode) await signOut(auth);
    router.push("/login");
  };

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <Link className="brand" href="/dashboard">
          <span className="brand-mark">P</span>
          <span>POWER AI</span>
        </Link>
        <nav>
          {nav.map(([href, vi, en]) => (
            <Link key={href} href={href} className={(href === "/learn" ? pathname.startsWith("/learn") : pathname === href) ? "nav-link active" : "nav-link"}>
              {language === "vi" ? vi : en}
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <button className="text-button" onClick={logout}>{language === "vi" ? "Đăng xuất" : "Sign out"}</button>
        </div>
      </aside>
      <main className="main-area">
        <header className="topbar">
          <div className="topbar-spacer" />
          <LanguageToggle />
        </header>
        <div className="page-wrap">{children}</div>
      </main>
    </div>
  );
}
