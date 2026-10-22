import { useQuery } from "@tanstack/react-query";
import { getTodayLog, todayLogQueryKey } from "../api/dailyLog";
import { todayIso } from "../utils/dates";

export function useTodayLog() {
  return useQuery({
    queryKey: todayLogQueryKey(todayIso()),
    queryFn: getTodayLog,
  });
}
