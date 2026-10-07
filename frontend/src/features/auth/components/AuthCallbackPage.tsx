import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";

import { useAuth } from "../useAuth";

export function AuthCallbackPage() {
  const [params] = useSearchParams();
  const { signInWithToken } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = params.get("token");
    if (!token) {
      setError("La respuesta de Google no incluyó un token válido.");
      return;
    }
    let active = true;
    signInWithToken(token)
      .then(() => {
        if (active) navigate("/dashboard", { replace: true });
      })
      .catch(() => {
        if (active) setError("No pudimos completar el inicio de sesión.");
      });
    return () => {
      active = false;
    };
  }, [params, signInWithToken, navigate]);

  return (
    <main className="flex min-h-full flex-col items-center justify-center gap-4 px-4 py-12">
      {error ? (
        <>
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
          <Button variant="secondary" onClick={() => navigate("/login", { replace: true })}>
            Volver al login
          </Button>
        </>
      ) : (
        <>
          <Spinner />
          <p className="text-sm text-slate-500">Completando el inicio de sesión…</p>
        </>
      )}
    </main>
  );
}