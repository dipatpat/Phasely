import { Outlet, useNavigate } from "react-router";
import { useAuth } from "../../auth/useAuth";
import { Sidebar, type NavItem } from "./Sidebar";

type AppShellProps = {
  navItems: NavItem[];
  roleLabel: string;
};

export function AppShell({ navItems, roleLabel }: AppShellProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  const userName = user ? `${user.first_name} ${user.last_name}` : "";

  return (
    <div className="app-shell">
      <Sidebar
        items={navItems}
        userName={userName}
        roleLabel={roleLabel}
        onLogout={handleLogout}
      />
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
