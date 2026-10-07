import { Outlet } from "react-router-dom";

import { ChatWidget } from "@/features/chat/components/ChatWidget";

import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

export function AppLayout() {
  return (
    <div className="flex min-h-full">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        <main className="flex-1 px-6 py-6">
          <Outlet />
        </main>
      </div>
      <ChatWidget />
    </div>
  );
}