# API Connection Test Guide

This guide walks you through testing the API connection between the React dashboard and Flask backend.

## Prerequisites

- Flask backend installed and configured
- React dashboard dependencies installed (`npm install` in dashboard/)
- Alpaca API keys configured in `.env` file

## Step 1: Start Flask Backend

Open a terminal in the project root and start the Flask backend:

```bash
# From stock-bot/ root directory
python src/main.py
```

**Expected Output:**

```
[INFO] Bot initialized successfully
[INFO] Dashboard running on http://127.0.0.1:5000
```

Keep this terminal running.

## Step 2: Start React Dev Server

Open a **second terminal** in the dashboard directory:

```bash
# From stock-bot/dashboard/ directory
npm run dev
```

**Expected Output:**

```
  VITE v7.2.2  ready in XXX ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

The dev server should start on port 3000 with Vite HMR enabled.

## Step 3: Open Browser and Test

1. Open your browser to: **http://localhost:3000**

2. You should see the API Test page with:

   - "Stock Trading Bot Dashboard - API Test" heading
   - A test component loading

3. The component will automatically test two API endpoints:
   - `/api/status` (Bot Status)
   - `/api/portfolio` (Portfolio Data)

## Expected Results

### ✅ Success Case

If the connection works, you'll see:

```
✅ All API Tests Passed!
Vite proxy working correctly

Bot Status Response:
{
  "is_running": false,
  "mode": "hybrid",
  "is_paper_trading": false,
  ...
}

Portfolio Response:
{
  "portfolio": { ... },
  "risk": { ... },
  "positions": [...],
  "performance": { ... }
}
```

### ❌ Failure Case

If the connection fails, you'll see:

```
❌ Errors:
• ❌ Bot Status failed: [error message]
• ❌ Portfolio failed: [error message]

Make sure Flask backend is running: python src/main.py
```

**Common Issues:**

1. **Flask not running** - Start Flask backend (Step 1)
2. **Port conflict** - Make sure ports 3000 and 5000 are available
3. **CORS errors** - Vite proxy should handle this automatically

## Step 4: Check Browser Console

Open Developer Tools (F12) and check the Console tab.

**Expected Console Output:**

```
Testing /api/status...
✅ Bot Status: {is_running: false, mode: "hybrid", ...}
Testing /api/portfolio...
✅ Portfolio: {portfolio: {...}, risk: {...}, ...}
```

## Step 5: Verify Network Requests

In Developer Tools, go to the **Network** tab:

1. Refresh the page (F5)
2. Look for requests to `/api/status` and `/api/portfolio`
3. Verify:
   - **Status Code**: 200 OK
   - **Response Type**: JSON
   - **Response Size**: Non-zero
   - **Request URL**: Should show `http://localhost:3000/api/...` (proxied to Flask)

## Troubleshooting

### Issue: "Failed to fetch" Error

**Cause**: Flask backend not running

**Solution**: Start Flask backend in first terminal

### Issue: 404 Not Found

**Cause**: Flask routes not registered or wrong endpoint

**Solution**: Verify Flask routes exist in `src/dashboard/app.py`

### Issue: Proxy Not Working

**Cause**: Vite proxy configuration issue

**Solution**:

1. Check `dashboard/vite.config.ts` has proxy config:
   ```typescript
   server: {
     port: 3000,
     proxy: {
       "/api": {
         target: "http://localhost:5000",
         changeOrigin: true,
       },
     },
   }
   ```
2. Restart Vite dev server

### Issue: TypeScript Errors

**Cause**: Type definitions don't match Flask API responses

**Solution**:

1. Check browser console for actual response structure
2. Update TypeScript types in `dashboard/src/types/` to match

## Next Steps After Successful Test

Once the API connection test passes:

1. **Remove Test Component** from `App.tsx`:

   ```typescript
   // Remove ApiTest import and component
   // Restore original App.tsx or keep clean slate for dashboard
   ```

2. **Delete Test Files** (optional):

   ```bash
   rm dashboard/src/components/ApiTest.tsx
   rm dashboard/API_TEST_GUIDE.md
   ```

3. **Proceed to Phase 3**: Utilities & Custom Hooks
   - Create formatting utilities (`format.ts`)
   - Build custom React hooks (`usePortfolio`, `useSignals`, etc.)
   - Set up Zustand store for UI state

## Phase 2 Complete ✅

If all tests pass, **Phase 2: Type Definitions & API Layer** is now complete:

- ✅ TypeScript types defined
- ✅ Base API client created
- ✅ All 18 Flask endpoints wrapped
- ✅ React Query configured
- ✅ API connection verified

**Ready for Phase 3!**
