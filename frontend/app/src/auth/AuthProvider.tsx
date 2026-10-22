import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import {
  getCurrentUser,
  logoutRequest,
  ME_QUERY_KEY,
  requestToken,
} from "../api/auth";
import type { User } from "../api/types";
import { AuthContext } from "./authContext";
import { clearToken, getToken, setToken } from "./tokenStorage";

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [hasToken, setHasToken] = useState(() => getToken() !== null);

  const me = useQuery({
    queryKey: ME_QUERY_KEY,
    queryFn: getCurrentUser,
    enabled: hasToken,
    staleTime: Infinity,
  });

  async function login(email: string, password: string): Promise<User> {
    const token = await requestToken(email, password);
    setToken(token.access_token);
    try {
      const user = await queryClient.fetchQuery({
        queryKey: ME_QUERY_KEY,
        queryFn: getCurrentUser,
      });
      setHasToken(true);
      return user;
    } catch (error) {
      clearToken();
      throw error;
    }
  }

  async function logout(): Promise<void> {
    try {
      await logoutRequest();
    } catch {
      // The token may already be expired; there is nothing left to revoke
    }
    clearToken();
    setHasToken(false);
    queryClient.clear();
  }

  const value = {
    user: hasToken ? (me.data ?? null) : null,
    isLoading: hasToken && me.isPending,
    login,
    logout,
  };

  return <AuthContext value={value}>{children}</AuthContext>;
}
