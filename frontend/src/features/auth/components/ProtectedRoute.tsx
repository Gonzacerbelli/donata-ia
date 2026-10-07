import { Navigate, useLocation } from "react-router-dom";

import { Spinner } from "@/components/ui/Spinner";

import { useAuth } from "../useAuth";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return (
      <div className="flex min-h-full items-center justify-center">
        <Spinner label="Verificando sesión" />
      </div>
    );
  }

  if (status === "anonymous") {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  }

  return <>{children}</>;
}