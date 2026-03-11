import { useState, useEffect } from "react";
import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/tasks", label: "タスク" },
  { to: "/projects", label: "プロジェクト" },
  { to: "/report/daily", label: "日別レポート" },
  { to: "/report/tasks", label: "タスク別レポート" },
];

function getInitialDark(): boolean {
  const saved = localStorage.getItem("theme");
  if (saved) return saved === "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export default function Layout() {
  const [dark, setDark] = useState(getInitialDark);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  return (
    <div className="min-h-screen bg-base-100 text-base-content">
      <div className="navbar bg-neutral text-neutral-content px-4">
        <div className="navbar-start">
          <span className="font-bold text-lg">工数管理</span>
        </div>
        <div className="navbar-center flex flex-wrap gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `btn btn-sm ${isActive ? "btn-primary" : "btn-ghost"}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>
        <div className="navbar-end">
          <button
            onClick={() => setDark((d) => !d)}
            className="btn btn-ghost btn-sm text-lg"
            title={dark ? "ライトモード" : "ダークモード"}
          >
            {dark ? "☀️" : "🌙"}
          </button>
        </div>
      </div>
      <main className="p-4 max-w-3xl mx-auto">
        <Outlet />
      </main>
    </div>
  );
}
