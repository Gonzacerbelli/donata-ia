import { createBrowserRouter, Navigate } from "react-router-dom";

import { ComingSoonPage } from "@/components/common/ComingSoonPage";
import { NotFoundPage } from "@/components/common/NotFoundPage";
import { AppLayout } from "@/components/layout/AppLayout";
import { AuthCallbackPage } from "@/features/auth/components/AuthCallbackPage";
import { LoginPage } from "@/features/auth/components/LoginPage";
import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { DashboardPage } from "@/features/dashboard/DashboardPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/auth/callback", element: <AuthCallbackPage /> },
  {
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      {
        path: "proveedores",
        element: <ComingSoonPage title="Proveedores" description="Alta, edición y baja de proveedores." />,
      },
      {
        path: "productos",
        element: (
          <ComingSoonPage title="Productos" description="Catálogo, precios y control de stock." />
        ),
      },
      {
        path: "clientes",
        element: <ComingSoonPage title="Clientes" description="Cartera de clientes y su historial." />,
      },
      {
        path: "ordenes",
        element: <ComingSoonPage title="Órdenes" description="Órdenes, pagos y estados." />,
      },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);