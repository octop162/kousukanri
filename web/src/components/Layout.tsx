import { useState, useEffect } from "react";
import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/tasks", label: "タスク" },
  { to: "/projects", label: "プロジェクト" },
  { to: "/report", label: "日次レポート" },
  { to: "/reports", label: "期間集計" },
  { to: "/reports-by-day", label: "日別レポート" },
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
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-800 dark:bg-gray-900 dark:text-gray-200">
      <nav className="relative px-4 py-2 flex flex-wrap gap-3 items-center justify-center bg-gray-800 text-gray-200 dark:bg-gray-950 dark:text-gray-300">
        <span className="font-bold mr-2">工数管理</span>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `px-2 py-1 rounded ${isActive ? "bg-blue-600 text-white dark:bg-blue-500" : "hover:bg-gray-700"}`
            }
          >
            {item.label}
          </NavLink>
        ))}
        <button
          onClick={() => setDark((d) => !d)}
          className="absolute right-3 text-lg hover:opacity-70"
          title={dark ? "ライトモード" : "ダークモード"}
        >
          {dark ? "☀️" : "🌙"}
        </button>
      </nav>
      <main className="p-4 max-w-3xl mx-auto">
        <Outlet />
      </main>
    </div>
  );
}
