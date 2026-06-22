import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { isAuthenticated } from "./lib/api";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { EventsPage } from "./pages/EventsPage";
import { HealthPage } from "./pages/HealthPage";
import { LoginPage } from "./pages/LoginPage";
import { MailboxesPage } from "./pages/MailboxesPage";
import { WebhooksPage } from "./pages/WebhooksPage";

function Protected({ children }: { children: React.ReactNode }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <Protected>
            <Layout />
          </Protected>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="mailboxes" element={<MailboxesPage />} />
        <Route path="webhooks" element={<WebhooksPage />} />
        <Route path="events" element={<EventsPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="health" element={<HealthPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
