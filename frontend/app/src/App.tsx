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
import { MealsPage } from "./pages/client/MealsPage";
import { WorkoutsPage } from "./pages/client/WorkoutsPage";
import { ClientDetailPage } from "./pages/trainer/ClientDetailPage";
import { ClientsPage } from "./pages/trainer/ClientsPage";
import { NutritionPlanPage } from "./pages/trainer/NutritionPlanPage";
import { TrainingPlanPage } from "./pages/trainer/TrainingPlanPage";
import { TrainerDashboardPage } from "./pages/trainer/TrainerDashboardPage";
import { ExerciseLibraryPage } from "./pages/trainer/ExerciseLibraryPage";
import { RecipeLibraryPage } from "./pages/trainer/RecipeLibraryPage";
import { BookSessionPage } from "./pages/client/BookSessionPage";
import { AvailabilityPage } from "./pages/trainer/AvailabilityPage";
import { SessionsPage } from "./pages/trainer/SessionsPage";

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
            <Route path="meals" element={<MealsPage />} />
            <Route path="workouts" element={<WorkoutsPage />} />
            <Route
              path="progress"
              element={<PlaceholderPage title="Progress" />}
            />
            <Route
              path="shopping-list"
              element={<PlaceholderPage title="Shopping list" />}
            />
            <Route path="sessions" element={<BookSessionPage />} />
          </Route>

          <Route
            path="/trainer"
            element={
              <RequireAuth role="trainer">
                <AppShell navItems={TRAINER_NAV} roleLabel="Personal Trainer" />
              </RequireAuth>
            }
          >
            <Route index element={<TrainerDashboardPage />} />
            <Route path="clients" element={<ClientsPage />} />
            <Route path="clients/:clientId" element={<ClientDetailPage />} />
            <Route
              path="clients/:clientId/nutrition"
              element={<NutritionPlanPage />}
            />
            <Route
              path="clients/:clientId/training"
              element={<TrainingPlanPage />}
            />

            <Route path="recipes" element={<RecipeLibraryPage />} />
            <Route path="exercises" element={<ExerciseLibraryPage />} />

            <Route path="sessions" element={<SessionsPage />} />
            <Route path="availability" element={<AvailabilityPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
