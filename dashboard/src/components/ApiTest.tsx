import { useEffect, useState } from "react";
import { getBotStatus } from "@/lib/api/bot";
import { getPortfolio } from "@/lib/api/portfolio";
import type { BotStatus, PortfolioResponse } from "@/types";

/**
 * Temporary component to test API connection with Flask backend.
 * This verifies the Vite proxy works and API responses match TypeScript types.
 *
 * To use: Add <ApiTest /> to App.tsx temporarily
 */
export function ApiTest() {
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function testApis() {
      const testErrors: string[] = [];

      // Test 1: Bot Status
      try {
        console.log("Testing /api/status...");
        const status = await getBotStatus();
        console.log("✅ Bot Status:", status);
        setBotStatus(status);
      } catch (error) {
        const msg = `❌ Bot Status failed: ${error}`;
        console.error(msg);
        testErrors.push(msg);
      }

      // Test 2: Portfolio
      try {
        console.log("Testing /api/portfolio...");
        const portfolioData = await getPortfolio();
        console.log("✅ Portfolio:", portfolioData);
        setPortfolio(portfolioData);
      } catch (error) {
        const msg = `❌ Portfolio failed: ${error}`;
        console.error(msg);
        testErrors.push(msg);
      }

      setErrors(testErrors);
      setLoading(false);
    }

    testApis();
  }, []);

  if (loading) {
    return (
      <div className="p-4 border rounded bg-blue-50">
        <h2 className="text-lg font-bold">API Connection Test</h2>
        <p>Testing API connection... Check browser console for details.</p>
      </div>
    );
  }

  return (
    <div className="p-4 border rounded bg-white">
      <h2 className="text-lg font-bold mb-4">API Connection Test Results</h2>

      {errors.length > 0 ? (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
          <h3 className="font-bold text-red-700">❌ Errors:</h3>
          <ul className="list-disc ml-5">
            {errors.map((error, i) => (
              <li key={i} className="text-red-600 text-sm">
                {error}
              </li>
            ))}
          </ul>
          <p className="mt-2 text-sm text-red-600">
            Make sure Flask backend is running: <code>python src/main.py</code>
          </p>
        </div>
      ) : (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded">
          <h3 className="font-bold text-green-700">✅ All API Tests Passed!</h3>
          <p className="text-sm text-green-600">Vite proxy working correctly</p>
        </div>
      )}

      {botStatus && (
        <div className="mb-4 p-3 border rounded">
          <h3 className="font-bold">Bot Status Response:</h3>
          <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
            {JSON.stringify(botStatus, null, 2)}
          </pre>
        </div>
      )}

      {portfolio && (
        <div className="mb-4 p-3 border rounded">
          <h3 className="font-bold">Portfolio Response:</h3>
          <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
            {JSON.stringify(portfolio, null, 2)}
          </pre>
        </div>
      )}

      <div className="mt-4 text-sm text-gray-600">
        <p>
          <strong>Next Steps:</strong>
        </p>
        <ul className="list-disc ml-5">
          <li>Remove this component from App.tsx</li>
          <li>Proceed to Phase 3: Utilities & Custom Hooks</li>
        </ul>
      </div>
    </div>
  );
}
