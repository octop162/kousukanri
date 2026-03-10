import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import TasksPage from "./pages/TasksPage";
import ProjectsPage from "./pages/ProjectsPage";
import ReportPage from "./pages/ReportPage";
import ReportsPage from "./pages/ReportsPage";
import ReportsByDayPage from "./pages/ReportsByDayPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/tasks" replace />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="projects" element={<ProjectsPage />} />
          <Route path="report" element={<ReportPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="reports-by-day" element={<ReportsByDayPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
