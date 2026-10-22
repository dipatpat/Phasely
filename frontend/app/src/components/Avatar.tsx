type AvatarProps = {
  firstName: string | null;
  lastName: string | null;
};

export function Avatar({ firstName, lastName }: AvatarProps) {
  const initials =
    `${firstName?.[0] ?? ""}${lastName?.[0] ?? ""}`.toUpperCase();
  return <span className="avatar">{initials || "?"}</span>;
}
