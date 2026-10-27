import { api, orNull } from "./client";
import type { IsoDate, ShoppingList, WeeklyReport } from "./types";

function weekParams(weekStart: IsoDate, clientId?: string): string {
  const params = new URLSearchParams({ week_start: weekStart });
  if (clientId) params.set("client_id", clientId);
  return params.toString();
}

export function weeklyReportQueryKey(weekStart: IsoDate, clientId?: string) {
  return ["weekly-report", clientId ?? "me", weekStart];
}

export function getWeeklyReport(
  weekStart: IsoDate,
  clientId?: string,
): Promise<WeeklyReport | null> {
  return orNull(
    api.get<WeeklyReport>(`/report/weekly?${weekParams(weekStart, clientId)}`),
  );
}

export function requestWeeklyReport(
  weekStart: IsoDate,
  clientId?: string,
): Promise<{ detail: string }> {
  return api.post<{ detail: string }>("/report/weekly", {
    week_start: weekStart,
    client_id: clientId ?? null,
  });
}

export function getShoppingList(
  weekStart: IsoDate,
  clientId?: string,
): Promise<ShoppingList> {
  return api.get<ShoppingList>(
    `/shopping-list/weekly?${weekParams(weekStart, clientId)}`,
  );
}
