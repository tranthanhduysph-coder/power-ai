"use client";

import { GoogleAuthProvider, signInWithEmailAndPassword, signInWithPopup } from "firebase/auth";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { auth } from "@/lib/firebase";

export default function LoginPage() {
  const router = useRouter();
  const { user, devMode } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (user || devMode) router.replace("/dashboard");
  }, [user, devMode, router]);

  const emailLogin = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await signInWithEmailAndPassword(auth, email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  };

  const googleLogin = async () => {
    setError("");
    try {
      await signInWithPopup(auth, new GoogleAuthProvider());
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google sign-in failed");
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand"><span className="brand-mark">P</span><strong>POWER AI</strong></div>
        <h1>Welcome back</h1>
        <p className="muted">Learn Biology with a structured POWER workflow.</p>
        <button className="button secondary full" onClick={googleLogin}>Continue with Google</button>
        <div className="divider"><span>or</span></div>
        <form onSubmit={emailLogin} className="form-stack">
          <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required /></label>
          <label>Password<input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required /></label>
          {error && <div className="error-box">{error}</div>}
          <button className="button primary full" type="submit">Sign in</button>
        </form>
        <p className="auth-foot">No account? <Link href="/register">Create one</Link></p>
      </div>
    </div>
  );
}
