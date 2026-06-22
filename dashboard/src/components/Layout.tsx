import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { clearTokens } from "../lib/api";
import { useDarkMode } from "../lib/theme";

const nav = [
  { to: "/", label: "Overview" },
  { to: "/mailboxes", label: "Mailboxes" },
  { to: "/webhooks", label: "Webhooks" },
  { to: "/events", label: "Events" },
  { to: "/analytics", label: "Analytics" },
  { to: "/health", label: "System" },
];

export function Layout() {
  const navigate = useNavigate();
  const { isDark, toggle } = useDarkMode();

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-52 flex-col border-r border-sidebar-border bg-sidebar text-slate-300">
        <div className="border-b border-sidebar-border px-4 py-4">
          <p className="text-sm font-semibold tracking-tight text-white">MailPulse</p>
          <p className="text-2xs text-slate-500">Email event platform</p>
        </div>
        <nav className="flex-1 space-y-0.5 p-2">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `block rounded-md px-3 py-2 text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-sidebar-hover text-white"
                    : "text-slate-400 hover:bg-sidebar-hover hover:text-white"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-sidebar-border p-3">
          <button
            type="button"
            className="w-full rounded-md px-3 py-1.5 text-left text-xs text-slate-400 transition-colors hover:bg-sidebar-hover hover:text-white"
            onClick={() => {
              clearTokens();
              navigate("/login");
            }}
          >
            Sign out
          </button>
          <button
            type="button"
            className="mt-2 flex w-full items-center justify-between rounded-md px-3 py-2 text-xs text-slate-400 transition-colors hover:bg-sidebar-hover hover:text-white"
            onClick={toggle}
          >
            <span>{isDark ? "Light mode" : "Dark mode"}</span>
            <span className={`h-2.5 w-2.5 rounded-full ${isDark ? "bg-emerald-400" : "bg-amber-300"}`} />
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <div className="mx-auto max-w-6xl px-6 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
