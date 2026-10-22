import { useQuery } from "@tanstack/react-query";
import {
  CLIENT_PROFILE_QUERY_KEY,
  getMyClientProfile,
} from "../api/clientProfile";

export function useClientProfile() {
  return useQuery({
    queryKey: CLIENT_PROFILE_QUERY_KEY,
    queryFn: getMyClientProfile,
  });
}
