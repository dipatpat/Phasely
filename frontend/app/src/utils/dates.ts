export function toIsoDate(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

export function todayIso(): string {
  return toIsoDate(new Date());
}

export function daysAgoIso(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return toIsoDate(date);
}

function parseDay(isoDate: string): Date {
  return new Date(`${isoDate}T00:00:00`);
}

export function formatRelativeDay(isoDate: string): string {
  const millisPerDay = 86_400_000;
  const days = Math.round(
    (parseDay(todayIso()).getTime() - parseDay(isoDate).getTime()) /
      millisPerDay,
  );
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  return `${days} days ago`;
}

export function formatShortDate(value: string): string {
  const date = value.length === 10 ? parseDay(value) : new Date(value);
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}

export function formatTime(date: Date): string {
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatLongDate(date: Date): string {
  return new Intl.DateTimeFormat("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(date);
}

export function greeting(date: Date): string {
  const hour = date.getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export function daysFromNowIso(days: number): string {
  return daysAgoIso(-days);
}

export function formatDayLabel(isoDate: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
  }).format(new Date(`${isoDate}T00:00:00`));
}

export function formatDateTime(value: string): string {
  const date = new Date(value);
  return `${formatDayLabel(toIsoDate(date))}, ${formatTime(date)}`;
}

export function shortTime(time: string): string {
  return time.slice(0, 5);
}
