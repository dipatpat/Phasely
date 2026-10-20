import { Outlet } from "react-router";
import { Sidebar, type NavItem } from "./Sidebar";

type AppShellProps = {
  navItems: NavItem[];
  userName: string;
  roleLabel: string;
};

export function AppShell({ navItems, userName, roleLabel }: AppShellProps) {
  return (
    <div className="app-shell">
      <Sidebar items={navItems} userName={userName} roleLabel={roleLabel} />
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
