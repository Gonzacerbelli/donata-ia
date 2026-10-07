import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { ApiError } from "@/lib/http";

import { exchangeAuthCode } from "../api";
import { useAuth } from "../useAuth";

export function AuthCallbackPage() {
  const [params] = useSearchParams();
  const { signInWithToken } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const startedRef = useRef(false);

  useEffect(() => {
    const oauthError = params.get("error");
    if (oauthError) {
      setError(oauthError);
      return;
    }
    const code = params.get("code");
    if (!code) {
      setError("La respuesta de Google no incluyó un código de acceso válido.");
      return;
    }
    if (startedRef.current) return;
    startedRef.current = true;
    exchangeAuthCode(code)
      .then(async (response) => {
        await signInWithToken(response.access_token);
        navigate("/dashboard", { replace: true });
      })
      .catch((cause) => {
        setError(
          cause instanceof ApiError ? cause.message : "No pudimos completar el inicio de sesión.",
        );
      });
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