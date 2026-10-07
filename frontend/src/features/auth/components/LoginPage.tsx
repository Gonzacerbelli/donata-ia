import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ApiError } from "@/lib/http";

import { fetchGoogleLoginUrl, login } from "../api";
import { useAuth } from "../useAuth";

const schema = z.object({
  username: z.string().min(1, "Ingresá tu usuario"),
  password: z.string().min(1, "Ingresá tu contraseña"),
});

type FieldErrors = Partial<Record<"username" | "password", string>>;

export function LoginPage() {
  const { signInWithToken } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  const redirectTo = (location.state as { from?: string } | null)?.from ?? "/dashboard";

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);

    const parsed = schema.safeParse({ username, password });
    if (!parsed.success) {
      const fieldErrors: FieldErrors = {};
      for (const issue of parsed.error.issues) {
        fieldErrors[issue.path[0] as keyof FieldErrors] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }
    setErrors({});
    setIsSubmitting(true);
    try {
      const response = await login(parsed.data);
      await signInWithToken(response.access_token);
      navigate(redirectTo, { replace: true });
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "No pudimos iniciar sesión.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleGoogle() {
    setFormError(null);
    setIsGoogleLoading(true);
    try {
      const url = await fetchGoogleLoginUrl();
      window.location.assign(url);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "No pudimos iniciar sesión.");
      setIsGoogleLoading(false);
    }
  }

  return (
    <main className="flex min-h-full items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold text-brand-700">Donata IA</h1>
          <p className="mt-1 text-sm text-slate-500">Gestión artesanal, asistida por IA</p>
        </div>

        <form
          onSubmit={handleSubmit}
          noValidate
          className="flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <Input
            label="Usuario"
            name="username"
            autoComplete="username"
            value={username}
            error={errors.username}
            onChange={(event) => setUsername(event.target.value)}
          />
          <Input
            label="Contraseña"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            error={errors.password}
            onChange={(event) => setPassword(event.target.value)}
          />

          {formError && (
            <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {formError}
            </p>
          )}

          <Button type="submit" isLoading={isSubmitting}>
            Ingresar
          </Button>

          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span className="h-px flex-1 bg-slate-200" />
            o
            <span className="h-px flex-1 bg-slate-200" />
          </div>

          <Button type="button" variant="secondary" isLoading={isGoogleLoading} onClick={handleGoogle}>
            Ingresar con Google
          </Button>
        </form>
      </div>
    </main>
  );
}