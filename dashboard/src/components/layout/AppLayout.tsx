import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";

export function AppLayout() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation bar at top */}
      <Navbar />

      {/* Main content area */}
      <main className="container mx-auto px-4 py-6 max-w-7xl">
        <Outlet />
      </main>
    </div>
  );
}
