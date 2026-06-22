import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { authApi, setTokens } from "../lib/api";
import { useDarkMode } from "../lib/theme";

export function LoginPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { isDark, toggle } = useDarkMode();

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const tokens =
        mode === "login"
          ? await authApi.login(email, password)
          : await authApi.register(email, password, fullName || undefined);
      setTokens(tokens);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-surface-muted px-4 dark:bg-slate-950">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.18),_transparent_35%),radial-gradient(circle_at_bottom_right,_rgba(14,165,233,0.12),_transparent_30%)] dark:bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.35),_transparent_35%),radial-gradient(circle_at_bottom_right,_rgba(14,165,233,0.18),_transparent_30%)]" />
      <button
        type="button"
        onClick={toggle}
        className="absolute right-4 top-4 z-10 inline-flex items-center gap-2 rounded-full border border-surface-border bg-surface px-3 py-2 text-xs font-semibold text-ink backdrop-blur transition-colors hover:bg-surface-muted dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-100 dark:hover:bg-slate-800"
      >
        <span
          className={`h-2.5 w-2.5 rounded-full ${isDark ? "bg-emerald-400" : "bg-amber-300"}`}
        />
        {isDark ? "Light mode" : "Dark mode"}
      </button>

      <div className="relative z-10 w-full max-w-sm rounded-2xl border border-surface-border bg-surface/95 p-6 shadow-2xl shadow-slate-950/10 backdrop-blur dark:border-slate-700/80 dark:bg-slate-950/90 dark:shadow-slate-950/40">
        <p className="text-sm font-semibold tracking-wide text-ink dark:text-slate-50">MailPulse</p>
        <p className="mt-1 text-xs text-ink-muted dark:text-slate-400">
          {mode === "login" ? "Sign in to your account" : "Create your account"}
        </p>
        <form className="mt-5 space-y-3" onSubmit={onSubmit}>
          {mode === "register" ? (
            <div>
              <label className="label">Full name</label>
              <input
                className="input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
          ) : null}
          <div>
            <label className="label">Email</label>
            <input
              className="input"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              className="input"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error ? <p className="text-2xs text-red-600 dark:text-red-400">{error}</p> : null}
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? "Please wait..." : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
        <button
          type="button"
          className="mt-4 w-full text-2xs text-ink-muted transition-colors hover:text-ink dark:text-slate-400 dark:hover:text-slate-200"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
        >
          {mode === "login"
            ? "Need an account? Register"
            : "Already have an account? Sign in"}
        </button>
      </div>
    </div>
  );
}
