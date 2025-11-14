/**
 * Bot Store - Zustand State Management
 *
 * Manages minimal client-side UI state for the application.
 * React Query handles server state, this store handles UI preferences.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { TradingMode } from "@/types";

/**
 * Bot Store State Interface
 */
interface BotStore {
  // UI State
  isSidebarOpen: boolean;
  selectedSymbol: string | null;

  // User Preferences
  preferredMode: TradingMode | null;
  autoRefreshEnabled: boolean;

  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setSelectedSymbol: (symbol: string | null) => void;
  setPreferredMode: (mode: TradingMode) => void;
  setAutoRefresh: (enabled: boolean) => void;
  reset: () => void;
}

/**
 * Initial state
 */
const initialState = {
  isSidebarOpen: true,
  selectedSymbol: null,
  preferredMode: null,
  autoRefreshEnabled: true,
};

/**
 * Bot Store Hook
 *
 * Provides access to UI state and actions.
 * State is persisted to localStorage automatically.
 *
 * @example
 * ```tsx
 * function Sidebar() {
 *   const { isSidebarOpen, toggleSidebar } = useBotStore();
 *
 *   return (
 *     <div>
 *       <button onClick={toggleSidebar}>
 *         {isSidebarOpen ? "Close" : "Open"} Sidebar
 *       </button>
 *     </div>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * function SymbolFilter() {
 *   const { selectedSymbol, setSelectedSymbol } = useBotStore();
 *
 *   return (
 *     <select
 *       value={selectedSymbol || ""}
 *       onChange={(e) => setSelectedSymbol(e.target.value || null)}
 *     >
 *       <option value="">All Symbols</option>
 *       <option value="PLTR">PLTR</option>
 *     </select>
 *   );
 * }
 * ```
 */
export const useBotStore = create<BotStore>()(
  persist(
    (set) => ({
      // Initial state
      ...initialState,

      // Actions
      toggleSidebar: () =>
        set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

      setSidebarOpen: (open: boolean) => set({ isSidebarOpen: open }),

      setSelectedSymbol: (symbol: string | null) =>
        set({ selectedSymbol: symbol }),

      setPreferredMode: (mode: TradingMode) => set({ preferredMode: mode }),

      setAutoRefresh: (enabled: boolean) =>
        set({ autoRefreshEnabled: enabled }),

      reset: () => set(initialState),
    }),
    {
      name: "bot-store", // localStorage key
    }
  )
);

/**
 * Selector Hooks for Optimized Re-renders
 *
 * Use these hooks to subscribe to specific state slices
 * and prevent unnecessary re-renders.
 */

/**
 * Hook to access sidebar state
 */
export const useSidebarState = () =>
  useBotStore((state) => ({
    isOpen: state.isSidebarOpen,
    toggle: state.toggleSidebar,
    setOpen: state.setSidebarOpen,
  }));

/**
 * Hook to access selected symbol
 */
export const useSelectedSymbol = () =>
  useBotStore((state) => ({
    symbol: state.selectedSymbol,
    setSymbol: state.setSelectedSymbol,
  }));

/**
 * Hook to access preferred trading mode
 */
export const usePreferredMode = () =>
  useBotStore((state) => ({
    mode: state.preferredMode,
    setMode: state.setPreferredMode,
  }));

/**
 * Hook to access auto-refresh setting
 */
export const useAutoRefresh = () =>
  useBotStore((state) => ({
    enabled: state.autoRefreshEnabled,
    setEnabled: state.setAutoRefresh,
  }));
