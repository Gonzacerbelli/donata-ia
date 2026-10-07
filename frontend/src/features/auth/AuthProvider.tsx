import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { setUnauthorizedHandler } from "@/lib/http";
import { tokenStore } from "@/lib/token";

import { fetchMe } from "./api";
import { AuthContext, type AuthStatus } from "./authContext";
import type { User } from "./types";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");
  const queryClient = useQueryClient();

  const logout = useCallback(() => {
    tokenStore.clear();
    setUser(null);
    setStatus("anonymous");
    queryClient.clear();
  }, [queryClient]);

  useEffect(() => {
    setUnauthorizedHandler(logout);
    return () => setUnauthorizedHandler(null);
  }, [logout]);

  const signInWithToken = useCallback(async (token: string) => {
    tokenStore.set(token);
    try {
      const me = await fetchMe();
      setUser(me);
      setStatus("authenticated");
    } catch (error) {
      tokenStore.clear();
      setUser(null);
      setStatus("anonymous");
      throw error;
    }
  }, []);

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      if (!tokenStore.get()) {
        setStatus("anonymous");
        return;
      }
      try {
        const me = await fetchMe();
        if (!active) return;
        setUser(me);
        setStatus("authenticated");
      } catch {
        if (!active) return;
        tokenStore.clear();
        setStatus("anonymous");
      }
    }

    void bootstrap();
    return () => {
      active = false;
    };
  }, []);

  const value = useMemo(
    () => ({ user, status, signInWithToken, logout }),
    [user, status, signInWithToken, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}