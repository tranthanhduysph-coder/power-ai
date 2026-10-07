"use client";

import { createUserWithEmailAndPassword, sendEmailVerification, updateProfile } from "firebase/auth";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { auth } from "@/lib/firebase";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (password !== confirm) return setError("Passwords do not match");
    try {
      const cred = await createUserWithEmailAndPassword(auth, email, password);
      await updateProfile(cred.user, { displayName: name });
      await sendEmailVerification(cred.user);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand"><span className="brand-mark">P</span><strong>POWER-AI-WEB</strong></div>
        <h1>Create account</h1>
        <form onSubmit={submit} className="form-stack">
          <label>Full name<input value={name} onChange={(e) => setName(e.target.value)} required /></label>
          <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required /></label>
          <label>Password<input value={password} onChange={(e) => setPassword(e.target.value)} type="password" minLength={6} required /></label>
          <label>Confirm password<input value={confirm} onChange={(e) => setConfirm(e.target.value)} type="password" minLength={6} required /></label>
          {error && <div className="error-box">{error}</div>}
          <button className="button primary full" type="submit">Create account</button>
        </form>
        <p className="auth-foot">Already registered? <Link href="/login">Sign in</Link></p>
        <p className="auth-legal">© 2026 Trần Thanh Duy · <Link href="/legal">Copyright & open source</Link></p>
      </div>
    </div>
  );
}
