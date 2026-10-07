import { createBrowserRouter, Navigate } from "react-router-dom";

import { NotFoundPage } from "@/components/common/NotFoundPage";
import { AppLayout } from "@/components/layout/AppLayout";
import { AuthCallbackPage } from "@/features/auth/components/AuthCallbackPage";
import { LoginPage } from "@/features/auth/components/LoginPage";
import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { ClientsPage } from "@/features/clients/components/ClientsPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { OrderCreatePage } from "@/features/orders/components/OrderCreatePage";
import { OrderDetailPage } from "@/features/orders/components/OrderDetailPage";
import { OrdersPage } from "@/features/orders/components/OrdersPage";
import { ProductsPage } from "@/features/products/components/ProductsPage";
import { ProvidersPage } from "@/features/providers/components/ProvidersPage";

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
      { path: "proveedores", element: <ProvidersPage /> },
      { path: "productos", element: <ProductsPage /> },
      { path: "clientes", element: <ClientsPage /> },
      { path: "ordenes", element: <OrdersPage /> },
      { path: "ordenes/nueva", element: <OrderCreatePage /> },
      { path: "ordenes/:id", element: <OrderDetailPage /> },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);