import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import { AppShell } from "./components/layout/AppShell";
import { CLIENT_NAV, TRAINER_NAV } from "./components/layout/navigation";
import { DevHomePage } from "./pages/DevHomePage";
import { PlaceholderPage } from "./pages/PlaceholderPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DevHomePage />} />

        <Route
          path="/client"
          element={
            <AppShell
              navItems={CLIENT_NAV}
              userName="Maria Nowak"
              roleLabel="Client"
            />
          }
        >
          <Route index element={<PlaceholderPage title="Today" />} />
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
            <AppShell
              navItems={TRAINER_NAV}
              userName="Anna Kowalska"
              roleLabel="Personal Trainer"
            />
          }
        >
          <Route index element={<PlaceholderPage title="Dashboard" />} />
          <Route path="clients" element={<PlaceholderPage title="Clients" />} />
          <Route path="recipes" element={<PlaceholderPage title="Recipes" />} />
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
    </BrowserRouter>
  );
}

export default App;
