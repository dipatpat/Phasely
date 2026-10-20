import { NavLink } from "react-router";

export type NavItem = {
  to: string;
  label: string;
  end?: boolean;
};

type SidebarProps = {
  items: NavItem[];
  userName: string;
  roleLabel: string;
  onLogout: () => void;
};

export function Sidebar({
  items,
  userName,
  roleLabel,
  onLogout,
}: SidebarProps) {
  return (
    <nav className="sidebar">
      <div className="logo">
        Phase<span>ly</span>
      </div>

      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) =>
            isActive ? "nav-item active" : "nav-item"
          }
        >
          {item.label}
        </NavLink>
      ))}

      <div className="sidebar-bottom">
        <strong>{userName}</strong>
        {roleLabel}
        <button type="button" className="btn-logout" onClick={onLogout}>
          ← Log out
        </button>
      </div>
    </nav>
  );
}
