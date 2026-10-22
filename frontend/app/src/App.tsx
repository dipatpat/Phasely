import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import { AuthProvider } from "./auth/AuthProvider";
import { HomeRedirect } from "./auth/HomeRedirect";
import { RequireAuth } from "./auth/RequireAuth";
import { AppShell } from "./components/layout/AppShell";
import { CLIENT_NAV, TRAINER_NAV } from "./components/layout/navigation";
import { LoginPage } from "./pages/auth/LoginPage";
import { RegisterPage } from "./pages/auth/RegisterPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { RequireClientProfile } from "./auth/RequireClientProfile";
import { OnboardingPage } from "./pages/client/OnboardingPage";
import { TodayPage } from "./pages/client/TodayPage";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route
            path="/onboarding"
            element={
              <RequireAuth role="client">
                <OnboardingPage />
              </RequireAuth>
            }
          />

          <Route
            path="/client"
            element={
              <RequireAuth role="client">
                <RequireClientProfile>
                  <AppShell navItems={CLIENT_NAV} roleLabel="Client" />
                </RequireClientProfile>
              </RequireAuth>
            }
          >
            <Route index element={<TodayPage />} />
            <Route path="meals" element={<PlaceholderPage title="Meals" />} />
            <Route
              path="workouts"
              element={<PlaceholderPage title="Workouts" />}
            />
            <Route
              path="progress"
              element={<PlaceholderPage title="Progress" />}
            />
            <Route
              path="shopping-list"
              element={<PlaceholderPage title="Shopping list" />}
            />
            <Route
              path="sessions"
              element={<PlaceholderPage title="Book session" />}
            />
          </Route>

          <Route
            path="/trainer"
            element={
              <RequireAuth role="trainer">
                <AppShell navItems={TRAINER_NAV} roleLabel="Personal Trainer" />
              </RequireAuth>
            }
          >
            <Route index element={<PlaceholderPage title="Dashboard" />} />
            <Route
              path="clients"
              element={<PlaceholderPage title="Clients" />}
            />
            <Route
              path="recipes"
              element={<PlaceholderPage title="Recipes" />}
            />
            <Route
              path="exercises"
              element={<PlaceholderPage title="Exercises" />}
            />
            <Route
              path="sessions"
              element={<PlaceholderPage title="Sessions" />}
            />
            <Route
              path="availability"
              element={<PlaceholderPage title="Availability" />}
            />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
