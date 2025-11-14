# Implementation Plan: React + shadcn/ui Dashboard Migration

## [Overview]

Migrate the current Flask-templated dashboard to a modern React + TypeScript + shadcn/ui frontend while keeping the existing Flask API backend unchanged. This is a frontend-only migration that replaces Jinja2 templates with a Vite-powered React application.

The AI Stock Trading Bot currently has a functional Python Flask dashboard (18 API endpoints, 5 HTML templates) that needs to be rebuilt as a modern React application. The Flask API backend will remain unchanged - this is purely a frontend migration focusing on DRY (Don't Repeat Yourself) and SOLID principles through proper component abstraction, centralized API management, and composable UI patterns.

**Current State:**

- Backend: Flask API with 18 REST endpoints serving JSON
- Current Frontend: Flask templates (Jinja2) with vanilla JavaScript
- Features: Portfolio monitoring, signal approval, trade history, bot control, settings management

**Target State:**

- Backend: Flask API (unchanged)
- New Frontend: Vite + React 18 + TypeScript + shadcn/ui + Tailwind CSS
- Architecture: React SPA → Flask REST API → Python Trading Bot

**Key Design Principles:**

1. **DRY**: Single source of truth for API calls, reusable components, shared utilities
2. **SOLID**: Single responsibility components, dependency injection via props/hooks, interface segregation
3. **Type Safety**: Full TypeScript coverage matching Flask API responses
4. **Composability**: Small, focused components that compose into features
5. **Separation of Concerns**: Clear boundaries between data fetching, business logic, and presentation

## [Types]

Define TypeScript types matching Flask API responses and domain models to ensure type safety across the application.

### Portfolio Types (`dashboard/src/types/portfolio.ts`)

```typescript
export interface PortfolioData {
  total_value: number;
  cash: number;
  positions_value: number;
  daily_pnl: number;
  daily_pnl_percent: number;
  buying_power: number;
}

export interface RiskMetrics {
  total_exposure: number;
  position_count: number;
  max_positions: number;
  daily_loss_limit: number;
  circuit_breaker_active: boolean;
}

export interface Position {
  symbol: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  market_value: number;
  stop_loss: number | null;
  trailing_stop: number | null;
}

export interface PerformanceMetrics {
  win_rate: number;
  total_trades: number;
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
}

export interface PortfolioResponse {
  portfolio: PortfolioData;
  risk: RiskMetrics;
  positions: Position[];
  performance: PerformanceMetrics;
}
```

### Trading Types (`dashboard/src/types/trading.ts`)

```typescript
export type TradingMode = "auto" | "manual" | "hybrid";
export type SignalType = "BUY" | "SELL" | "LONG" | "SHORT";
export type SignalStatus = "pending" | "approved" | "rejected" | "executed";
export type OrderSide = "buy" | "sell";
export type OrderType = "market" | "limit";
export type TimeInForce = "day" | "gtc" | "ioc" | "fok";

export interface TradingSignal {
  id: number;
  symbol: string;
  signal_type: SignalType;
  confidence: number;
  predicted_direction: string;
  entry_price: number;
  suggested_quantity: number;
  features: string;
  timestamp: string;
}

export interface Trade {
  id: number;
  symbol: string;
  action: string;
  quantity: number;
  entry_price: number;
  exit_price: number | null;
  pnl: number;
  pnl_percent: number;
  status: string;
  entry_time: string;
  exit_time: string | null;
  stop_loss: number | null;
  confidence: number | null;
}

export interface Order {
  id: string;
  symbol: string;
  side: OrderSide;
  type: OrderType;
  quantity: number;
  limit_price: number | null;
  stop_price: number | null;
  time_in_force: TimeInForce;
  submitted_at: string;
}

export interface PlaceOrderRequest {
  symbol: string;
  side: OrderSide;
  quantity: number;
  type: OrderType;
  limit_price?: number;
  time_in_force?: TimeInForce;
}

export interface TradeFilters {
  symbol?: string;
  days?: number;
  status?: string;
  include_archived?: boolean;
}
```

### Bot Types (`dashboard/src/types/bot.ts`)

```typescript
export interface BotStatus {
  is_running: boolean;
  mode: TradingMode;
  is_paper_trading: boolean;
  uptime: number;
  last_cycle: string | null;
  market_open: boolean;
}

export interface BotSettings {
  trading: {
    mode: TradingMode;
    symbols: string[];
    close_positions_eod: boolean;
  };
  risk: {
    risk_per_trade: number;
    max_position_size: number;
    max_portfolio_exposure: number;
    daily_loss_limit: number;
    stop_loss_percent: number;
    trailing_stop_percent: number;
    trailing_stop_activation: number;
  };
  ml: {
    model_path: string;
    sequence_length: number;
    prediction_confidence_threshold: number;
    auto_execute_threshold: number;
    retrain_frequency: string;
  };
  is_paper_trading: boolean;
}
```

### API Response Types (`dashboard/src/types/api.ts`)

```typescript
export interface ApiResponse<T = unknown> {
  success?: boolean;
  message?: string;
  error?: string;
  data?: T;
}

export interface ApiError {
  error: string;
  status?: number;
}
```

## [Files]

Complete file structure for the new React dashboard application, organized by concern and following single responsibility principle.

### New Project Root: `dashboard/`

**Purpose**: Separate React application from Flask backend  
**Location**: `stock-bot/dashboard/` (sibling to `src/`)

### Configuration Files (Root Level)

**`dashboard/package.json`**

- Purpose: npm dependencies and scripts
- Contains: React, Vite, TypeScript, TanStack Query, Zustand, shadcn/ui dependencies

**`dashboard/tsconfig.json`**

- Purpose: TypeScript compiler configuration
- Contains: Strict mode, path aliases (@/), React JSX settings

**`dashboard/vite.config.ts`**

- Purpose: Vite build tool configuration
- Contains: React plugin, path resolution, proxy to Flask API (localhost:5000)

**`dashboard/tailwind.config.ts`**

- Purpose: Tailwind CSS configuration
- Contains: shadcn/ui theme, custom colors, dark mode settings

**`dashboard/components.json`**

- Purpose: shadcn/ui CLI configuration
- Contains: Component install paths, style preferences

**`dashboard/.eslintrc.cjs`**

- Purpose: ESLint code quality rules
- Contains: React hooks rules, TypeScript rules

**`dashboard/.prettierrc`**

- Purpose: Code formatting configuration
- Contains: Tailwind plugin for class sorting

**`dashboard/index.html`**

- Purpose: HTML entry point
- Contains: Root div, Vite script tag

**`dashboard/.gitignore`**

- Purpose: Exclude build artifacts
- Contains: node_modules/, dist/, .env.local

### Source Directory: `dashboard/src/`

**`dashboard/src/main.tsx`**

- Purpose: React application entry point
- Mounts React app, provides QueryClientProvider

**`dashboard/src/App.tsx`**

- Purpose: Root component with routing
- Contains: React Router setup, route definitions, layout

**`dashboard/src/index.css`**

- Purpose: Global styles
- Contains: Tailwind directives, CSS variables, global resets

**`dashboard/src/vite-env.d.ts`**

- Purpose: Vite TypeScript declarations
- Auto-generated by Vite

### Type Definitions: `dashboard/src/types/`

**`portfolio.ts`** - Portfolio domain types (see Types section)  
**`trading.ts`** - Trading domain types (see Types section)  
**`bot.ts`** - Bot control types (see Types section)  
**`api.ts`** - API response types (see Types section)

### API Layer: `dashboard/src/lib/api/`

**`client.ts`**

- Purpose: Base HTTP client with error handling
- Exports: `apiClient` object with get/post/put/delete methods

**`portfolio.ts`**

- Purpose: Portfolio-related API calls
- Exports: `getPortfolio()`

**`trading.ts`**

- Purpose: Trading-related API calls
- Exports: `getOrders()`, `placeOrder()`, `cancelOrder()`, `closePosition()`, `closeAllPositions()`, `getTrades()`

**`signals.ts`**

- Purpose: Signal-related API calls
- Exports: `getPendingSignals()`, `approveSignal()`, `rejectSignal()`, `getSignalHistory()`

**`bot.ts`**

- Purpose: Bot control API calls
- Exports: `getBotStatus()`, `startBot()`, `stopBot()`, `emergencyStop()`, `setTradingMode()`, `getSettings()`, `updateSettings()`, `syncWithAlpaca()`

**`queries.ts`**

- Purpose: React Query configuration
- Exports: Query keys, query functions for React Query hooks

### Custom Hooks: `dashboard/src/lib/hooks/`

**`usePortfolio.ts`**

- Purpose: Portfolio data management
- Returns: `{ data, isLoading, error, refetch }`

**`useSignals.ts`**

- Purpose: Signals management
- Returns: `{ signals, approve, reject, isApproving, isRejecting }`

**`useTrades.ts`**

- Purpose: Trades data with filtering
- Returns: `{ trades, isLoading, error }`

**`useBot.ts`**

- Purpose: Bot status and control
- Returns: `{ status, isLoading, error }`, `{ start, stop, setMode, emergencyStop }`

### Utilities: `dashboard/src/lib/utils/`

**`format.ts`**

- Purpose: Formatting utilities (DRY)
- Exports: `formatCurrency()`, `formatPercent()`, `formatDate()`, `formatNumber()`

**`cn.ts`**

- Purpose: Tailwind class merging utility (from shadcn/ui)
- Exports: `cn()` function

### State Management: `dashboard/src/store/`

**`bot-store.ts`**

- Purpose: Zustand store for minimal app-wide state
- Contains: UI state (sidebar, filters), bot mode preference

### Layout Components: `dashboard/src/components/layout/`

**`AppLayout.tsx`**

- Purpose: Main layout wrapper
- Children: Navbar, main content area, footer

**`Navbar.tsx`**

- Purpose: Top navigation bar
- Features: Brand logo, navigation links, bot status badge

### Shared Components: `dashboard/src/components/shared/`

**`BotStatusBadge.tsx`**

- Purpose: Reusable bot status indicator
- Props: `{ status: BotStatus }`

**`LoadingSpinner.tsx`**

- Purpose: Loading state indicator
- Props: `{ size?: 'sm' | 'md' | 'lg' }`

**`ErrorMessage.tsx`**

- Purpose: Error display component
- Props: `{ error: string | Error }`

**`EmptyState.tsx`**

- Purpose: No data placeholder
- Props: `{ icon?: ReactNode, message: string }`

**`ConfirmDialog.tsx`**

- Purpose: Confirmation modal (DRY for destructive actions)
- Props: `{ title, message, onConfirm, onCancel }`

### Dashboard Feature Components: `dashboard/src/components/dashboard/`

**`PortfolioSummary.tsx`**

- Purpose: Portfolio value cards
- Uses: Card component from shadcn/ui
- Data: Portfolio data from usePortfolio hook

**`RiskMetrics.tsx`**

- Purpose: Risk gauges and warnings
- Uses: Progress bar, Alert components
- Data: Risk metrics from usePortfolio hook

**`PositionsTable.tsx`**

- Purpose: Active positions table
- Uses: Table component from shadcn/ui
- Actions: Close position button

**`PendingSignalsTable.tsx`**

- Purpose: Signals awaiting approval
- Uses: Table, Button components
- Actions: Approve/reject buttons

**`PendingOrdersTable.tsx`**

- Purpose: Open orders display
- Uses: Table component
- Actions: Cancel order button

**`PerformanceCards.tsx`**

- Purpose: Performance metrics display
- Uses: Card component
- Data: Performance from usePortfolio hook

**`BotControls.tsx`**

- Purpose: Bot start/stop/mode controls
- Uses: Button, Select components
- Actions: Start, stop, mode change, emergency stop

**`PlaceOrderModal.tsx`**

- Purpose: Manual order placement form
- Uses: Dialog, Form components
- Validation: Risk checks before submission

### Page Components: `dashboard/src/pages/`

**`DashboardPage.tsx`**

- Purpose: Main dashboard page
- Composes: PortfolioSummary, RiskMetrics, PositionsTable, PendingSignalsTable, PendingOrdersTable, PerformanceCards

**`TradesPage.tsx`**

- Purpose: Trade history page
- Features: Filters, sorting, trade table

**`SignalsPage.tsx`**

- Purpose: Signal history and management
- Features: Signal table with outcomes, accuracy metrics

**`SettingsPage.tsx`**

- Purpose: Bot configuration page
- Features: Settings forms for trading, risk, ML parameters

### UI Components: `dashboard/src/components/ui/`

**shadcn/ui components** (installed via CLI):

- `button.tsx`, `card.tsx`, `table.tsx`, `dialog.tsx`, `select.tsx`, `tabs.tsx`, `toast.tsx`, `badge.tsx`, `dropdown-menu.tsx`, `progress.tsx`, `alert.tsx`, `form.tsx`, `input.tsx`, `label.tsx`

These are copied into the project and can be customized.

## [Functions]

Key functions organized by module, following single responsibility principle.

### API Client (`dashboard/src/lib/api/client.ts`)

**`createApiClient(baseUrl: string)`**

- Purpose: Factory function for API client instance
- Returns: Object with HTTP methods
- Responsibility: Centralize API configuration (DRY)

**`apiClient.get<T>(endpoint: string, options?: RequestInit): Promise<T>`**

- Purpose: Perform GET request with type safety
- Error Handling: Catches network errors, parses API errors
- Responsibility: Standardize GET requests

**`apiClient.post<T>(endpoint: string, data: any, options?: RequestInit): Promise<T>`**

- Purpose: Perform POST request with JSON body
- Error Handling: Same as GET
- Responsibility: Standardize POST requests

**`apiClient.put<T>(endpoint: string, data: any, options?: RequestInit): Promise<T>`**

- Purpose: Perform PUT request
- Responsibility: Standardize PUT requests

**`apiClient.delete<T>(endpoint: string, options?: RequestInit): Promise<T>`**

- Purpose: Perform DELETE request
- Responsibility: Standardize DELETE requests

### Portfolio API (`dashboard/src/lib/api/portfolio.ts`)

**`getPortfolio(): Promise<PortfolioResponse>`**

- Purpose: Fetch complete portfolio data
- Endpoint: `GET /api/portfolio`
- Returns: Portfolio, risk, positions, performance
- Error Handling: Throws ApiError on failure

### Trading API (`dashboard/src/lib/api/trading.ts`)

**`getOrders(): Promise<Order[]>`**

- Purpose: Fetch pending orders
- Endpoint: `GET /api/orders`

**`placeOrder(request: PlaceOrderRequest): Promise<ApiResponse<{ order_id: string }>>`**

- Purpose: Place new market or limit order
- Endpoint: `POST /api/orders/create`
- Validation: Symbol, side, quantity required

**`cancelOrder(orderId: string): Promise<ApiResponse<void>>`**

- Purpose: Cancel pending order
- Endpoint: `POST /api/orders/${orderId}/cancel`

**`closePosition(symbol: string): Promise<ApiResponse<void>>`**

- Purpose: Close specific position
- Endpoint: `POST /api/positions/${symbol}/close`

**`closeAllPositions(): Promise<ApiResponse<{ closed: string[] }>>`**

- Purpose: Close all open positions
- Endpoint: `POST /api/positions/close-all`
- Returns: List of closed symbols

**`getTrades(filters?: TradeFilters): Promise<Trade[]>`**

- Purpose: Fetch trade history with optional filters
- Endpoint: `GET /api/trades/history?symbol=...&days=...`
- Filters: Symbol, date range, status

### Signals API (`dashboard/src/lib/api/signals.ts`)

**`getPendingSignals(): Promise<TradingSignal[]>`**

- Purpose: Fetch signals awaiting approval
- Endpoint: `GET /api/signals/pending`

**`approveSignal(signalId: number): Promise<ApiResponse<void>>`**

- Purpose: Approve trading signal
- Endpoint: `POST /api/signals/${signalId}/approve`

**`rejectSignal(signalId: number): Promise<ApiResponse<void>>`**

- Purpose: Reject trading signal
- Endpoint: `POST /api/signals/${signalId}/reject`

**`getSignalHistory(days: number): Promise<TradingSignal[]>`**

- Purpose: Fetch historical signals
- Endpoint: `GET /api/signals/history?days=${days}`

### Bot Control API (`dashboard/src/lib/api/bot.ts`)

**`getBotStatus(): Promise<BotStatus>`**

- Purpose: Fetch current bot state
- Endpoint: `GET /api/status`

**`startBot(): Promise<ApiResponse<void>>`**

- Purpose: Start trading bot
- Endpoint: `POST /api/bot/start`

**`stopBot(): Promise<ApiResponse<void>>`**

- Purpose: Stop trading bot
- Endpoint: `POST /api/bot/stop`

**`emergencyStop(): Promise<ApiResponse<{ positions_closed: number }>>`**

- Purpose: Emergency stop with position closure
- Endpoint: `POST /api/bot/emergency-stop`

**`setTradingMode(mode: TradingMode): Promise<ApiResponse<void>>`**

- Purpose: Change trading mode
- Endpoint: `POST /api/bot/mode`
- Body: `{ mode: 'auto' | 'manual' | 'hybrid' }`

**`getSettings(): Promise<BotSettings>`**

- Purpose: Fetch bot configuration
- Endpoint: `GET /api/settings`

**`updateSettings(settings: Partial<BotSettings>): Promise<ApiResponse<void>>`**

- Purpose: Update bot settings
- Endpoint: `POST /api/settings`
- Body: Partial settings object

**`syncWithAlpaca(): Promise<ApiResponse<any>>`**

- Purpose: Trigger manual database-Alpaca sync
- Endpoint: `POST /api/bot/sync`

### Formatting Utilities (`dashboard/src/lib/utils/format.ts`)

**`formatCurrency(value: number): string`**

- Purpose: Format number as USD currency
- Example: `10000.50` → `"$10,000.50"`
- Responsibility: Single formatting logic (DRY)

**`formatPercent(value: number): string`**

- Purpose: Format number as percentage
- Example: `2.5` → `"2.50%"`

**`formatDate(date: string | Date): string`**

- Purpose: Format date/time string
- Example: `"2025-11-13T21:00:00Z"` → `"Nov 13, 2025, 9:00 PM"`

**`formatNumber(value: number, decimals?: number): string`**

- Purpose: Format number with commas
- Example: `12345.678` → `"12,345.68"`

### React Query Hooks (`dashboard/src/lib/hooks/`)

**`usePortfolio(refetchInterval?: number)`**

- Purpose: Manage portfolio data with auto-refresh
- Uses: `useQuery` from React Query
- Returns: `{ data: PortfolioResponse, isLoading, error, refetch }`
- Default Refetch: 30 seconds

**`useSignals()`**

- Purpose: Manage signals with approve/reject mutations
- Uses: `useQuery` + `useMutation`
- Returns: `{ signals, approve, reject, isApproving, isRejecting }`
- Invalidates: Queries on mutation success

**`useTrades(filters?: TradeFilters)`**

- Purpose: Fetch trade history with filters
- Uses: `useQuery`
- Returns: `{ trades, isLoading, error }`
- Dependency: Re-fetches when filters change

**`useBotStatus()`**

- Purpose: Fetch bot status
- Uses: `useQuery`
- Returns: `{ status: BotStatus, isLoading, error }`

**`useBotControl()`**

- Purpose: Control bot with mutations
- Uses: `useMutation` for start/stop/mode
- Returns: `{ start, stop, setMode, emergencyStop, isLoading }`
- Side Effect: Invalidates bot status query

## [Classes]

No traditional classes - using functional components and hooks following modern React patterns. This section explains the architectural approach instead.

### Component Architecture Pattern

All components follow functional component pattern with hooks:

```typescript
export function ComponentName({ prop1, prop2 }: ComponentProps) {
  // 1. State hooks
  const [localState, setLocalState] = useState<Type>()

  // 2. Query hooks (server state)
  const { data, isLoading } = useQuery(...)

  // 3. Mutation hooks
  const mutation = useMutation(...)

  // 4. Effect hooks (if needed)
  useEffect(() => { ... }, [deps])

  // 5. Event handlers
  const handleAction = useCallback(() => { ... }, [deps])

  // 6. Render
  return <div>...</div>
}
```

### Component Categories

**Layout Components** - Structural, composition-focused

- Single Responsibility: Layout structure only
- Examples: `AppLayout`, `Navbar`

**Feature Components** - Business logic, data-driven

- Single Responsibility: One feature per component
- Examples: `PortfolioSummary`, `PositionsTable`, `BotControls`
- Pattern: Fetch data with hooks, pass to presentation components

**UI Components** (shadcn/ui) - Primitive, reusable

- Single Responsibility: One UI pattern per component
- Examples: `Button`, `Card`, `Table`, `Dialog`
- Owned Code: Copied into project, fully customizable

**Shared Components** - Cross-cutting concerns

- Single Responsibility: One utility per component
- Examples: `LoadingSpinner`, `ErrorMessage`, `EmptyState`

### State Management Approach

**Server State**: React Query (TanStack Query)

- Manages: API data, caching, refetching
- Why: Server state is fundamentally different from UI state
- Benefits: Built-in loading/error states, automatic cache invalidation

**Client State**: Zustand

- Manages: UI preferences, sidebar state, selected filters
- Why: Minimal boilerplate, no provider hell
- Pattern:

  ```typescript
  interface BotStore {
    mode: TradingMode;
    isSidebarOpen: boolean;
    setMode: (mode: TradingMode) => void;
    toggleSidebar: () => void;
  }

  export const useBotStore = create<BotStore>((set) => ({ ... }))
  ```

**Local State**: useState

- Manages: Form inputs, toggle states, component-specific state
- Why: Closest to component, no overhead

### Dependency Injection Pattern

Components receive dependencies via props/hooks:

```typescript
// Bad: Hard-coded dependency
function BotControls() {
  const api = new BotApi(); // Tight coupling
  return <div>...</div>;
}

// Good: Dependency injection via hooks
function BotControls() {
  const { status, start, stop } = useBotControl(); // Abstraction
  return <div>...</div>;
}
```

This follows **Dependency Inversion Principle**: Depend on abstractions (hooks) not implementations (direct API calls).

### Why No Classes?

1. **Hooks replace lifecycle methods** - useEffect instead of componentDidMount
2. **Composition over inheritance** - Compose hooks instead of extending classes
3. **No "this" binding issues** - Cleaner, less error-prone
4. **Better tree-shaking** - Functions are easier to optimize
5. **Aligns with SOLID** - Functions are naturally single-purpose

## [Dependencies]

All required npm packages with versions, purposes, and installation commands.

### Core Dependencies

```json
{
  "react": "^18.3.1",
  "react-dom": "^18.3.1",
  "react-router-dom": "^7.0.2",
  "typescript": "^5.6.2"
}
```

### Build Tool

```json
{
  "vite": "^6.0.1",
  "@vitejs/plugin-react": "^4.3.4"
}
```

### State & Data Fetching

```json
{
  "@tanstack/react-query": "^5.62.8",
  "zustand": "^5.0.2"
}
```

**Rationale**:

- React Query: Industry standard for server state (caching, refetching, mutations)
- Zustand: Minimal UI state (simpler than Redux, no provider wrapper)

### UI Framework

```json
{
  "tailwindcss": "^3.4.15",
  "tailwind-merge": "^2.5.5",
  "clsx": "^2.1.1",
  "class-variance-authority": "^0.7.1"
}
```

**Radix UI Primitives** (for shadcn/ui):

```json
{
  "@radix-ui/react-slot": "^1.1.1",
  "@radix-ui/react-dialog": "^1.1.2",
  "@radix-ui/react-dropdown-menu": "^2.1.2",
  "@radix-ui/react-select": "^2.1.2",
  "@radix-ui/react-tabs": "^1.1.1",
  "@radix-ui/react-toast": "^1.2.2",
  "@radix-ui/react-progress": "^1.1.1",
  "@radix-ui/react-alert-dialog": "^1.1.2"
}
```

**Icons**:

```json
{
  "lucide-react": "^0.469.0"
}
```

### Dev Dependencies

```json
{
  "@types/react": "^18.3.14",
  "@types/react-dom": "^18.3.1",
  "@types/node": "^22.10.2",
  "eslint": "^9.16.0",
  "@typescript-eslint/eslint-plugin": "^8.18.2",
  "@typescript-eslint/parser": "^8.18.2",
  "eslint-plugin-react-hooks": "^5.1.0",
  "eslint-plugin-react-refresh": "^0.4.16",
  "prettier": "^3.4.2",
  "prettier-plugin-tailwindcss": "^0.6.10",
  "postcss": "^8.4.49",
  "autoprefixer": "^10.4.20"
}
```

### Installation Steps

**1. Create Vite Project**:

```bash
cd stock-bot
npm create vite@latest dashboard -- --template react-ts
cd dashboard
npm install
```

**2. Install Core Dependencies**:

```bash
npm install react-router-dom @tanstack/react-query zustand
```

**3. Install Tailwind CSS**:

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**4. Initialize shadcn/ui**:

```bash
npx shadcn@latest init
```

Configuration selections:

- Style: Default
- Base color: Slate
- CSS variables: Yes
- React Server Components: No
- Location: `src/components/ui`
- Tailwind config: `tailwind.config.ts`
- Import alias: `@/*`

**5. Install shadcn/ui Components**:

```bash
npx shadcn@latest add button card table dialog select tabs toast badge dropdown-menu progress alert form input label
```

**6. Install Icons**:

```bash
npm install lucide-react
```

### Package.json Scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "format": "prettier --write \"src/**/*.{ts,tsx,css,md}\""
  }
}
```

### Vite Configuration for Flask API Proxy

**`dashboard/vite.config.ts`**:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:5000",
        changeOrigin: true,
      },
    },
  },
});
```

This proxies all `/api/*` requests from React dev server (port 3000) to Flask (port 5000).

## [Testing]

Testing strategy focusing on critical paths, component behavior, and API integration.

### Testing Stack

**Framework**: Vitest (Vite-native test runner, Jest-compatible API)  
**React Testing**: @testing-library/react (behavior-driven component testing)  
**API Mocking**: MSW (Mock Service Worker - intercepts network requests)  
**User Simulation**: @testing-library/user-event (realistic user interactions)

### Installation

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom msw@latest
```

### Test Structure

```
dashboard/src/
├── __tests__/
│   ├── setup.ts                 # Test environment setup
│   ├── mocks/
│   │   ├── handlers.ts          # MSW request handlers
│   │   ├── data.ts              # Mock data fixtures
│   │   └── server.ts            # MSW server setup
│   ├── components/
│   │   ├── BotControls.test.tsx
│   │   ├── PortfolioSummary.test.tsx
│   │   └── PositionsTable.test.tsx
│   ├── hooks/
│   │   ├── usePortfolio.test.ts
│   │   ├── useSignals.test.ts
│   │   └── useBotControl.test.ts
│   ├── utils/
│   │   └── format.test.ts
│   └── integration/
│       ├── dashboard-flow.test.tsx
│       └── signal-approval.test.tsx
```

### Configuration Files

**`dashboard/vitest.config.ts`**:

```typescript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/__tests__/setup.ts"],
    css: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/__tests__/**",
        "src/components/ui/**", // shadcn/ui components
        "src/types/**",
        "src/main.tsx",
      ],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
```

**`dashboard/src/__tests__/setup.ts`**:

```typescript
import { expect, afterEach } from "vitest";
import { cleanup } from "@testing-library/react";
import * as matchers from "@testing-library/jest-dom/matchers";
import { server } from "./mocks/server";

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers);

// Start MSW server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));

// Reset handlers after each test
afterEach(() => {
  cleanup();
  server.resetHandlers();
});

// Clean up after all tests
afterAll(() => server.close());
```

### MSW Mock Setup

**`dashboard/src/__tests__/mocks/data.ts`**:

```typescript
import type {
  PortfolioResponse,
  TradingSignal,
  Trade,
  BotStatus,
} from "@/types";

export const mockPortfolio: PortfolioResponse = {
  portfolio: {
    total_value: 50000.0,
    cash: 15000.0,
    positions_value: 35000.0,
    daily_pnl: 1250.5,
    daily_pnl_percent: 2.56,
    buying_power: 45000.0,
  },
  risk: {
    total_exposure: 70.0,
    position_count: 3,
    max_positions: 5,
    daily_loss_limit: 1000.0,
    circuit_breaker_active: false,
  },
  positions: [
    {
      symbol: "AAPL",
      quantity: 50,
      entry_price: 180.0,
      current_price: 185.5,
      unrealized_pnl: 275.0,
      unrealized_pnl_percent: 3.06,
      market_value: 9275.0,
      stop_loss: 171.0,
      trailing_stop: null,
    },
  ],
  performance: {
    win_rate: 65.5,
    total_trades: 42,
    profit_factor: 1.85,
    sharpe_ratio: 1.42,
    max_drawdown: -8.3,
  },
};

export const mockSignals: TradingSignal[] = [
  {
    id: 1,
    symbol: "TSLA",
    signal_type: "BUY",
    confidence: 0.78,
    predicted_direction: "up",
    entry_price: 245.3,
    suggested_quantity: 20,
    features: '{"rsi": 42, "macd": 1.5}',
    timestamp: "2025-11-13T20:00:00Z",
  },
];

export const mockTrades: Trade[] = [
  {
    id: 1,
    symbol: "MSFT",
    action: "BUY",
    quantity: 10,
    entry_price: 380.0,
    exit_price: 395.5,
    pnl: 155.0,
    pnl_percent: 4.08,
    status: "closed",
    entry_time: "2025-11-12T14:30:00Z",
    exit_time: "2025-11-13T15:45:00Z",
    stop_loss: 361.0,
    confidence: 0.82,
  },
];

export const mockBotStatus: BotStatus = {
  is_running: true,
  mode: "hybrid",
  is_paper_trading: false,
  uptime: 3600,
  last_cycle: "2025-11-13T20:30:00Z",
  market_open: true,
};
```

**`dashboard/src/__tests__/mocks/handlers.ts`**:

```typescript
import { http, HttpResponse } from "msw";
import { mockPortfolio, mockSignals, mockTrades, mockBotStatus } from "./data";

export const handlers = [
  // Portfolio
  http.get("/api/portfolio", () => {
    return HttpResponse.json(mockPortfolio);
  }),

  // Signals
  http.get("/api/signals/pending", () => {
    return HttpResponse.json(mockSignals);
  }),

  http.post("/api/signals/:id/approve", ({ params }) => {
    return HttpResponse.json({ success: true, message: "Signal approved" });
  }),

  http.post("/api/signals/:id/reject", ({ params }) => {
    return HttpResponse.json({ success: true, message: "Signal rejected" });
  }),

  // Trades
  http.get("/api/trades/history", () => {
    return HttpResponse.json(mockTrades);
  }),

  // Bot Control
  http.get("/api/status", () => {
    return HttpResponse.json(mockBotStatus);
  }),

  http.post("/api/bot/start", () => {
    return HttpResponse.json({ success: true, message: "Bot started" });
  }),

  http.post("/api/bot/stop", () => {
    return HttpResponse.json({ success: true, message: "Bot stopped" });
  }),

  http.post("/api/bot/emergency-stop", () => {
    return HttpResponse.json({
      success: true,
      message: "Emergency stop executed",
      positions_closed: 3,
    });
  }),
];
```

**`dashboard/src/__tests__/mocks/server.ts`**:

```typescript
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
```

### Test Examples

#### Unit Test: Formatting Utilities

**`dashboard/src/__tests__/utils/format.test.ts`**:

```typescript
import { describe, it, expect } from "vitest";
import {
  formatCurrency,
  formatPercent,
  formatNumber,
} from "@/lib/utils/format";

describe("formatCurrency", () => {
  it("formats positive numbers correctly", () => {
    expect(formatCurrency(10000.5)).toBe("$10,000.50");
    expect(formatCurrency(1234.56)).toBe("$1,234.56");
  });

  it("formats negative numbers correctly", () => {
    expect(formatCurrency(-500.25)).toBe("-$500.25");
  });

  it("handles zero", () => {
    expect(formatCurrency(0)).toBe("$0.00");
  });
});

describe("formatPercent", () => {
  it("formats percentages with 2 decimals", () => {
    expect(formatPercent(2.5678)).toBe("2.57%");
    expect(formatPercent(-1.234)).toBe("-1.23%");
  });
});

describe("formatNumber", () => {
  it("formats numbers with commas", () => {
    expect(formatNumber(1234567.89)).toBe("1,234,567.89");
  });

  it("respects decimal places", () => {
    expect(formatNumber(123.456789, 2)).toBe("123.46");
  });
});
```

#### Component Test: BotControls

**`dashboard/src/__tests__/components/BotControls.test.tsx`**:

```typescript
import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BotControls } from "@/components/dashboard/BotControls";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const wrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("BotControls", () => {
  it("displays bot status correctly", async () => {
    render(<BotControls />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/running/i)).toBeInTheDocument();
      expect(screen.getByText(/hybrid/i)).toBeInTheDocument();
    });
  });

  it("handles start button click", async () => {
    const user = userEvent.setup();
    render(<BotControls />, { wrapper });

    const startButton = await screen.findByRole("button", { name: /start/i });
    await user.click(startButton);

    await waitFor(() => {
      expect(screen.getByText(/bot started/i)).toBeInTheDocument();
    });
  });

  it("shows confirmation dialog for emergency stop", async () => {
    const user = userEvent.setup();
    render(<BotControls />, { wrapper });

    const emergencyButton = await screen.findByRole("button", {
      name: /emergency stop/i,
    });
    await user.click(emergencyButton);

    expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
  });
});
```

#### Hook Test: usePortfolio

**`dashboard/src/__tests__/hooks/usePortfolio.test.ts`**:

```typescript
import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { usePortfolio } from "@/lib/hooks/usePortfolio";
import { mockPortfolio } from "../mocks/data";

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("usePortfolio", () => {
  it("fetches portfolio data successfully", async () => {
    const { result } = renderHook(() => usePortfolio(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockPortfolio);
    expect(result.current.error).toBeNull();
  });

  it("handles errors correctly", async () => {
    // Override handler to return error
    server.use(
      http.get("/api/portfolio", () => {
        return HttpResponse.json({ error: "Server error" }, { status: 500 });
      })
    );

    const { result } = renderHook(() => usePortfolio(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });
  });
});
```

#### Integration Test: Signal Approval Flow

**`dashboard/src/__tests__/integration/signal-approval.test.tsx`**:

```typescript
import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DashboardPage } from "@/pages/DashboardPage";

describe("Signal Approval Flow", () => {
  it("approves a signal and refreshes the list", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const user = userEvent.setup();

    render(
      <QueryClientProvider client={queryClient}>
        <DashboardPage />
      </QueryClientProvider>
    );

    // Wait for signals to load
    await waitFor(() => {
      expect(screen.getByText("TSLA")).toBeInTheDocument();
    });

    // Click approve button
    const approveButton = screen.getByRole("button", { name: /approve/i });
    await user.click(approveButton);

    // Verify success message
    await waitFor(() => {
      expect(screen.getByText(/signal approved/i)).toBeInTheDocument();
    });

    // Verify signal is removed from list (refetch happens)
    await waitFor(() => {
      expect(screen.queryByText("TSLA")).not.toBeInTheDocument();
    });
  });
});
```

### Testing Patterns & Best Practices

**1. Test User Behavior, Not Implementation**

```typescript
// ❌ Bad: Testing implementation details
expect(component.state.isOpen).toBe(true);

// ✅ Good: Testing user-visible behavior
expect(screen.getByRole("dialog")).toBeInTheDocument();
```

**2. Use MSW for API Mocking**

- Mock at the network level, not the function level
- Tests work with real API client code
- Easy to add/modify endpoints

**3. Arrange-Act-Assert Pattern**

```typescript
it("closes position successfully", async () => {
  // Arrange
  render(<PositionsTable />, { wrapper });
  const user = userEvent.setup();

  // Act
  const closeButton = await screen.findByRole("button", { name: /close/i });
  await user.click(closeButton);

  // Assert
  await waitFor(() => {
    expect(screen.getByText(/position closed/i)).toBeInTheDocument();
  });
});
```

**4. Test Critical Paths**

Focus on:

- Portfolio data loading and display
- Signal approval/rejection
- Bot start/stop operations
- Order placement and cancellation
- Emergency stop functionality

**5. Accessibility Testing**

Use `@testing-library/react` queries that enforce accessibility:

```typescript
// Prefer accessible queries
screen.getByRole("button", { name: /start bot/i });
screen.getByLabelText(/symbol/i);
screen.getByText(/portfolio value/i);

// Avoid
screen.getByTestId("start-button"); // Last resort only
```

### Running Tests

```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch

# Run specific test file
npm test -- PositionsTable.test.tsx
```

### Test Coverage Goals

- **Utilities**: 100% coverage (pure functions, easy to test)
- **Hooks**: 90%+ coverage (core business logic)
- **Components**: 70%+ coverage (focus on critical user interactions)
- **Integration**: Key user flows covered (signal approval, bot control, order placement)

## [Implementation Order]

Step-by-step execution plan organized into phases. Each phase builds upon the previous one, with validation checkpoints to ensure stability before proceeding.

### Phase 1: Project Setup & Configuration

**Goal**: Bootstrap React application with proper tooling and configuration.

**Step 1.1**: Create Vite React TypeScript Project

```bash
cd stock-bot
npm create vite@latest dashboard -- --template react-ts
cd dashboard
npm install
```

**Validation**: `npm run dev` starts dev server on port 5173

**Step 1.2**: Configure Tailwind CSS

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Update `tailwind.config.ts`:

```typescript
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {} },
  plugins: [],
};
```

Update `src/index.css` with Tailwind directives.

**Validation**: Run dev server, verify Tailwind classes work

**Step 1.3**: Initialize shadcn/ui

```bash
npx shadcn@latest init
```

Configuration:

- Style: Default
- Base color: Slate
- CSS variables: Yes
- Import alias: `@/*`

**Validation**: Check `components.json` created, `src/lib/utils.ts` exists

**Step 1.4**: Configure Vite for Flask API Proxy

Update `vite.config.ts`:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:5000",
        changeOrigin: true,
      },
    },
  },
});
```

**Validation**: Proxy will be tested in Phase 2

**Step 1.5**: Install Core Dependencies

```bash
npm install react-router-dom @tanstack/react-query zustand lucide-react
```

**Validation**: Check `package.json` has all dependencies

**Step 1.6**: Install shadcn/ui Components

```bash
npx shadcn@latest add button card table dialog select tabs toast badge dropdown-menu progress alert form input label
```

**Validation**: Check `src/components/ui/` directory populated

**Step 1.7**: Set Up TypeScript Configuration

Update `tsconfig.json` if needed for strict mode:

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true
  }
}
```

**Phase 1 Checkpoint**: ✅ Dev server runs, Tailwind works, shadcn/ui components available

---

### Phase 2: Type Definitions & API Layer

**Goal**: Establish type safety and centralized API communication.

**Step 2.1**: Create Type Definition Files

Create directory structure:

```bash
mkdir -p src/types
```

Create files (use content from [Types] section):

- `src/types/portfolio.ts`
- `src/types/trading.ts`
- `src/types/bot.ts`
- `src/types/api.ts`

**Validation**: No TypeScript errors, types export correctly

**Step 2.2**: Create API Client

```bash
mkdir -p src/lib/api
```

Create `src/lib/api/client.ts` with base HTTP client.

**Validation**: Can import `apiClient` in other files

**Step 2.3**: Implement API Modules

Create API files (use content from [Functions] section):

- `src/lib/api/portfolio.ts`
- `src/lib/api/trading.ts`
- `src/lib/api/signals.ts`
- `src/lib/api/bot.ts`

**Validation**: Each module exports expected functions

**Step 2.4**: Test API Connection

Start Flask backend:

```bash
cd ..  # Back to stock-bot root
python src/main.py
```

In dashboard, create test file:

```typescript
// src/test-api.ts
import { getBotStatus } from "./lib/api/bot";

getBotStatus()
  .then((status) => console.log("Bot Status:", status))
  .catch((err) => console.error("API Error:", err));
```

Run: `npx vite-node src/test-api.ts`

**Validation**: API call succeeds, proxy works, data returns

**Step 2.5**: Set Up React Query

Create `src/lib/api/queries.ts` with query keys and configurations.

**Validation**: Query keys defined for all endpoints

**Phase 2 Checkpoint**: ✅ Types defined, API client working, Flask API reachable

---

### Phase 3: Utilities & Custom Hooks

**Goal**: Build reusable utilities and data-fetching hooks.

**Step 3.1**: Create Formatting Utilities

```bash
mkdir -p src/lib/utils
```

Create `src/lib/utils/format.ts` (see [Functions] section).

**Validation**: Write quick unit tests or console.log checks

**Step 3.2**: Implement Custom Hooks

```bash
mkdir -p src/lib/hooks
```

Create hooks (use content from [Functions] section):

- `src/lib/hooks/usePortfolio.ts`
- `src/lib/hooks/useSignals.ts`
- `src/lib/hooks/useTrades.ts`
- `src/lib/hooks/useBotControl.ts`

**Validation**: Hooks compile, export correct return types

**Step 3.3**: Set Up Zustand Store

Create `src/store/bot-store.ts` for minimal UI state.

**Validation**: Store can be imported and used

**Phase 3 Checkpoint**: ✅ Utilities and hooks ready for component use

---

### Phase 4: Layout & Shared Components

**Goal**: Build application structure and reusable UI components.

**Step 4.1**: Create Layout Components

```bash
mkdir -p src/components/layout
```

Create:

- `src/components/layout/AppLayout.tsx`
- `src/components/layout/Navbar.tsx`

**Validation**: Layout renders with empty content

**Step 4.2**: Create Shared Components

```bash
mkdir -p src/components/shared
```

Create:

- `src/components/shared/BotStatusBadge.tsx`
- `src/components/shared/LoadingSpinner.tsx`
- `src/components/shared/ErrorMessage.tsx`
- `src/components/shared/EmptyState.tsx`
- `src/components/shared/ConfirmDialog.tsx`

**Validation**: Each component renders correctly in isolation

**Step 4.3**: Set Up React Router

Update `src/App.tsx` with routing structure:

```typescript
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<div>Dashboard Page</div>} />
          <Route path="trades" element={<div>Trades Page</div>} />
          <Route path="signals" element={<div>Signals Page</div>} />
          <Route path="settings" element={<div>Settings Page</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

**Validation**: Navigate between routes, layout persists

**Step 4.4**: Set Up React Query Provider

Update `src/main.tsx`:

```typescript
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      refetchOnWindowFocus: false,
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);
```

**Validation**: App runs without errors

**Phase 4 Checkpoint**: ✅ Layout working, routing functional, providers set up

---

### Phase 5: Dashboard Feature Components

**Goal**: Implement main dashboard page with portfolio, risk, positions, and signals.

**Step 5.1**: Create Dashboard Component Directory

```bash
mkdir -p src/components/dashboard
```

**Step 5.2**: Build Portfolio Summary Component

Create `src/components/dashboard/PortfolioSummary.tsx`

- Use `usePortfolio` hook
- Display portfolio cards (total value, cash, P&L)
- Use `Card` from shadcn/ui

**Validation**: Component fetches data, displays portfolio values

**Step 5.3**: Build Risk Metrics Component

Create `src/components/dashboard/RiskMetrics.tsx`

- Display risk gauges
- Show circuit breaker status
- Use `Progress` and `Alert` components

**Validation**: Risk metrics display correctly

**Step 5.4**: Build Positions Table Component

Create `src/components/dashboard/PositionsTable.tsx`

- Display active positions in table
- Add "Close Position" button
- Use `Table` component from shadcn/ui

**Validation**: Positions render, close button works

**Step 5.5**: Build Pending Signals Table Component

Create `src/components/dashboard/PendingSignalsTable.tsx`

- Use `useSignals` hook
- Display pending signals
- Add Approve/Reject buttons
- Show confidence scores

**Validation**: Signals display, approve/reject mutations work

**Step 5.6**: Build Pending Orders Table Component

Create `src/components/dashboard/PendingOrdersTable.tsx`

- Display open orders
- Add "Cancel Order" button

**Validation**: Orders display, cancel button works

**Step 5.7**: Build Performance Cards Component

Create `src/components/dashboard/PerformanceCards.tsx`

- Display win rate, Sharpe ratio, profit factor, max drawdown
- Use `Card` component

**Validation**: Performance metrics display

**Step 5.8**: Build Bot Controls Component

Create `src/components/dashboard/BotControls.tsx`

- Use `useBotControl` hook
- Start/Stop/Mode buttons
- Emergency stop with confirmation
- Display current status

**Validation**: Bot controls work, mode changes persist

**Step 5.9**: Compose Dashboard Page

Create `src/pages/DashboardPage.tsx`

- Import all dashboard components
- Arrange in grid layout
- Add loading states

**Validation**: Full dashboard loads, all features work

**Phase 5 Checkpoint**: ✅ Dashboard page complete and functional

---

### Phase 6: Additional Pages

**Goal**: Implement Trades, Signals, and Settings pages.

**Step 6.1**: Create Pages Directory

```bash
mkdir -p src/pages
```

**Step 6.2**: Build Trades History Page

Create `src/pages/TradesPage.tsx`

- Use `useTrades` hook with filters
- Display trade history table
- Add filter controls (symbol, date range, status)
- Show P&L with color coding

**Validation**: Trades display, filters work

**Step 6.3**: Build Signals History Page

Create `src/pages/SignalsPage.tsx`

- Display signal history
- Show signal outcomes (approved/rejected/executed)
- Calculate signal accuracy metrics
- Add date range filter

**Validation**: Signal history displays with outcomes

**Step 6.4**: Build Settings Page

Create `src/pages/SettingsPage.tsx`

- Use `useSettings` hook (create if needed)
- Forms for trading, risk, ML settings
- Use `Form`, `Input`, `Label` components
- Add save button with validation

**Validation**: Settings load, form submits, settings update

**Step 6.5**: Build Place Order Modal

Create `src/components/dashboard/PlaceOrderModal.tsx`

- Manual order entry form
- Symbol, side, quantity, type inputs
- Validation before submission
- Use `Dialog` component

**Validation**: Modal opens, order placement works

**Phase 6 Checkpoint**: ✅ All pages implemented

---

### Phase 7: Polish & Enhancements

**Goal**: Add finishing touches, error handling, and user experience improvements.

**Step 7.1**: Add Toast Notifications

Set up `Toaster` component in `App.tsx`.
Add success/error toasts to all mutations.

**Validation**: Toasts appear on actions

**Step 7.2**: Implement Error Boundaries

Create error boundary component for graceful error handling.

**Validation**: App doesn't crash on errors

**Step 7.3**: Add Loading Skeletons

Replace generic loading spinners with skeleton components for better UX.

**Validation**: Skeletons match component shapes

**Step 7.4**: Implement Dark Mode (Optional)

Add dark mode toggle using Tailwind dark mode.

**Validation**: Theme switches correctly

**Step 7.5**: Optimize Re-renders

Add React.memo to expensive components.
Use useCallback for event handlers.

**Validation**: Check React DevTools Profiler

**Step 7.6**: Add Keyboard Shortcuts (Optional)

Implement shortcuts for common actions (e.g., Cmd+K for search).

**Validation**: Shortcuts work

**Phase 7 Checkpoint**: ✅ App polished and production-ready

---

### Phase 8: Testing

**Goal**: Add test coverage for critical paths.

**Step 8.1**: Install Testing Dependencies

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom msw@latest
```

**Step 8.2**: Set Up Test Configuration

Create `vitest.config.ts` (see [Testing] section).
Create `src/__tests__/setup.ts`.

**Validation**: `npm test` runs

**Step 8.3**: Set Up MSW Mocks

Create mock data and handlers (see [Testing] section):

- `src/__tests__/mocks/data.ts`
- `src/__tests__/mocks/handlers.ts`
- `src/__tests__/mocks/server.ts`

**Validation**: Mock server starts in tests

**Step 8.4**: Write Unit Tests

Test formatting utilities:

- `src/__tests__/utils/format.test.ts`

**Validation**: Tests pass

**Step 8.5**: Write Hook Tests

Test custom hooks:

- `src/__tests__/hooks/usePortfolio.test.ts`
- `src/__tests__/hooks/useSignals.test.ts`

**Validation**: Tests pass

**Step 8.6**: Write Component Tests

Test critical components:

- `src/__tests__/components/BotControls.test.tsx`
- `src/__tests__/components/PortfolioSummary.test.tsx`
- `src/__tests__/components/PositionsTable.test.tsx`

**Validation**: Component tests pass

**Step 8.7**: Write Integration Tests

Test user flows:

- `src/__tests__/integration/signal-approval.test.tsx`
- `src/__tests__/integration/dashboard-flow.test.tsx`

**Validation**: Integration tests pass

**Step 8.8**: Run Full Test Suite

```bash
npm test -- --coverage
```

Review coverage report, aim for targets specified in [Testing] section.

**Validation**: All tests pass, coverage meets goals

**Phase 8 Checkpoint**: ✅ Test suite complete, coverage adequate

---

### Phase 9: Documentation & Deployment

**Goal**: Document the application and prepare for deployment.

**Step 9.1**: Create README for Dashboard

Create `dashboard/README.md`:

- Project overview
- Tech stack
- Setup instructions
- Available scripts
- Development workflow
- Testing commands
- Deployment instructions

**Validation**: README is clear and complete

**Step 9.2**: Add JSDoc Comments

Add JSDoc comments to complex functions and hooks.

**Validation**: Key functions documented

**Step 9.3**: Build Production Bundle

```bash
npm run build
```

**Validation**: Build succeeds, no errors

**Step 9.4**: Test Production Build

```bash
npm run preview
```

Start Flask backend, test all features work with production build.

**Validation**: Production build works correctly

**Step 9.5**: Update Root README

Update `stock-bot/README.md` to include dashboard setup instructions.

**Validation**: Root README updated

**Phase 9 Checkpoint**: ✅ Documentation complete, production-ready

---

### Phase 10: Final Validation

**Goal**: Comprehensive testing and verification before launch.

**Step 10.1**: Flask API Endpoint Coverage Verification

Verify all 18 Flask endpoints are used:

- `/api/portfolio` ✓
- `/api/orders` ✓
- `/api/orders/create` ✓
- `/api/orders/:id/cancel` ✓
- `/api/positions/:symbol/close` ✓
- `/api/positions/close-all` ✓
- `/api/trades/history` ✓
- `/api/signals/pending` ✓
- `/api/signals/:id/approve` ✓
- `/api/signals/:id/reject` ✓
- `/api/signals/history` ✓
- `/api/status` ✓
- `/api/bot/start` ✓
- `/api/bot/stop` ✓
- `/api/bot/emergency-stop` ✓
- `/api/bot/mode` ✓
- `/api/settings` ✓
- `/api/bot/sync` ✓

**Validation**: All endpoints integrated

**Step 10.2**: Feature Parity Check

Compare new React dashboard with original Flask dashboard:

- Portfolio monitoring ✓
- Risk metrics display ✓
- Active positions table ✓
- Pending signals approval ✓
- Pending orders management ✓
- Trade history with filters ✓
- Signal history with outcomes ✓
- Bot controls (start/stop/mode) ✓
- Emergency stop functionality ✓
- Settings management ✓
- Performance metrics ✓

**Validation**: All features migrated

**Step 10.3**: Cross-Browser Testing

Test in:

- Chrome
- Firefox
- Safari
- Edge

**Validation**: Works across browsers

**Step 10.4**: Responsive Design Check

Test at different screen sizes:

- Desktop (1920x1080)
- Laptop (1366x768)
- Tablet (768x1024)
- Mobile (375x667)

**Validation**: Responsive at all sizes

**Step 10.5**: Accessibility Audit

Run Lighthouse accessibility audit.
Fix any critical issues.

**Validation**: Accessibility score >90

**Step 10.6**: Performance Audit

Run Lighthouse performance audit.
Optimize if needed.

**Validation**: Performance score >85

**Step 10.7**: Final Manual Testing

Perform end-to-end manual testing:

1. Start Flask backend
2. Start React dev server
3. Test complete workflow:
   - View portfolio
   - Approve signal
   - Monitor trade execution
   - Close position
   - Check trade history
   - Update settings
   - Test emergency stop

**Validation**: Complete workflow functions correctly

**Phase 10 Checkpoint**: ✅ Application fully validated, ready for production

---

## Implementation Summary

### Total Phases: 10

1. **Project Setup & Configuration** - Bootstrap and tooling
2. **Type Definitions & API Layer** - Type safety and API communication
3. **Utilities & Custom Hooks** - Reusable utilities and data hooks
4. **Layout & Shared Components** - Application structure
5. **Dashboard Feature Components** - Main dashboard page
6. **Additional Pages** - Trades, signals, settings pages
7. **Polish & Enhancements** - UX improvements
8. **Testing** - Test coverage
9. **Documentation & Deployment** - Docs and production build
10. **Final Validation** - Comprehensive testing

### Estimated Timeline

- **Phase 1-2**: 2-3 hours (setup and foundation)
- **Phase 3-4**: 3-4 hours (utilities and layout)
- **Phase 5**: 4-6 hours (dashboard implementation)
- **Phase 6**: 3-4 hours (additional pages)
- **Phase 7**: 2-3 hours (polish)
- **Phase 8**: 3-4 hours (testing)
- **Phase 9**: 1-2 hours (documentation)
- **Phase 10**: 2-3 hours (validation)

**Total: 20-30 hours** for complete implementation

### Key Success Criteria

✅ All 18 Flask API endpoints integrated  
✅ Type-safe TypeScript throughout  
✅ DRY principles applied (no code duplication)  
✅ SOLID principles followed (single responsibility)  
✅ All original dashboard features migrated  
✅ Test coverage meets goals (70%+ components, 90%+ hooks)  
✅ Responsive design works on all devices  
✅ Accessibility score >90  
✅ Performance score >85  
✅ Cross-browser compatibility

### Next Steps After Completion

1. Monitor production performance
2. Gather user feedback
3. Iterate based on feedback
4. Consider adding:
   - Real-time WebSocket updates
   - Advanced charting (TradingView integration)
   - Mobile app (React Native)
   - Multi-account support
   - Advanced analytics dashboard

---

**Plan Status**: ✅ COMPLETE - Ready for execution
