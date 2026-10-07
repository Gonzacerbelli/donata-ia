import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { AuthContext, type AuthContextValue } from "../authContext";
import { ProtectedRoute } from "./ProtectedRoute";

function renderWithAuth(overrides: Partial<AuthContextValue>) {
  const value: AuthContextValue = {
    user: null,
    status: "anonymous",
    signInWithToken: async () => {},
    logout: () => {},
    ...overrides,
  };

  return render(
    <AuthContext.Provider value={value}>
      <MemoryRouter initialEntries={["/privada"]}>
        <Routes>
          <Route path="/login" element={<div>Pantalla de login</div>} />
          <Route
            path="/privada"
            element={
              <ProtectedRoute>
                <div>Contenido protegido</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

describe("ProtectedRoute", () => {
  it("redirige al login cuando no hay sesión", () => {
    renderWithAuth({ status: "anonymous" });
    expect(screen.getByText("Pantalla de login")).toBeInTheDocument();
    expect(screen.queryByText("Contenido protegido")).not.toBeInTheDocument();
  });

  it("renderiza el contenido cuando hay sesión", () => {
    renderWithAuth({
      status: "authenticated",
      user: { id: "u1", email: "a@b.com", name: "Test", picture: null },
    });
    expect(screen.getByText("Contenido protegido")).toBeInTheDocument();
  });

  it("muestra el estado de verificación mientras carga", () => {
    renderWithAuth({ status: "loading" });
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});