import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import TasksPage from "./pages/TasksPage";
import ProjectsPage from "./pages/ProjectsPage";
import ReportDailyPage from "./pages/ReportDailyPage";
import ReportTasksPage from "./pages/ReportTasksPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/tasks?simple=1" replace />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="projects" element={<ProjectsPage />} />
          <Route path="report/daily" element={<ReportDailyPage />} />
          <Route path="report/tasks" element={<ReportTasksPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
