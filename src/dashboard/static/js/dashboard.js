// ============================================================================
// AI Trading Bot Dashboard - Shared JavaScript
// ============================================================================

// Utility Functions
// ============================================================================

/**
 * Format a number as currency (USD)
 */
function formatCurrency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

/**
 * Format a number as percentage
 */
function formatPercentage(value) {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value / 100);
}

/**
 * Format a date string
 */
function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Toast Notifications
// ============================================================================

/**
 * Show a toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type of toast (success, error, warning, info)
 * @param {number} duration - Duration in milliseconds (default 3000)
 */
function showToast(message, type = "info", duration = 3000) {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  // Auto-remove after duration
  setTimeout(() => {
    toast.style.animation = "slideIn 0.3s ease-out reverse";
    setTimeout(() => {
      container.removeChild(toast);
    }, 300);
  }, duration);
}

// Bot Status Management
// ============================================================================

/**
 * Update bot status indicator
 */
async function updateBotStatus() {
  try {
    const response = await fetch("/api/status");
    const data = await response.json();

    const statusIndicator = document.getElementById("botStatus");
    if (!statusIndicator) return;

    const statusDot = statusIndicator.querySelector(".status-dot");
    const statusText = statusIndicator.querySelector(".status-text");

    if (data.is_running) {
      statusDot.classList.add("active");
      statusText.textContent = `Running (${data.mode})`;

      // Update button visibility
      const startBtn = document.getElementById("startBtn");
      const stopBtn = document.getElementById("stopBtn");
      if (startBtn && stopBtn) {
        startBtn.style.display = "none";
        stopBtn.style.display = "inline-block";
      }
    } else {
      statusDot.classList.remove("active");
      statusText.textContent = "Stopped";

      // Update button visibility
      const startBtn = document.getElementById("startBtn");
      const stopBtn = document.getElementById("stopBtn");
      if (startBtn && stopBtn) {
        startBtn.style.display = "inline-block";
        stopBtn.style.display = "none";
      }
    }
  } catch (error) {
    console.error("Error updating bot status:", error);
  }
}

// Position Management
// ============================================================================

/**
 * Close a position
 * @param {string} symbol - Symbol to close
 */
async function closePosition(symbol) {
  if (!confirm(`Close position for ${symbol}?`)) {
    return;
  }

  try {
    // Note: This would need to be implemented in the Flask API
    showToast(`Closing position ${symbol}...`, "info");
    // For now, just show a message
    // In a real implementation, you'd call the API to close the position
  } catch (error) {
    showToast("Error closing position", "error");
  }
}

// API Error Handling
// ============================================================================

/**
 * Handle API errors consistently
 * @param {Response} response - Fetch response object
 */
async function handleApiError(response) {
  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.error || "API request failed");
  }
  return response.json();
}

// Initialize
// ============================================================================

/**
 * Initialize dashboard on page load
 */
document.addEventListener("DOMContentLoaded", function () {
  // Update bot status on load
  updateBotStatus();

  // Update bot status every 30 seconds
  setInterval(updateBotStatus, 30000);
});

// Export functions for use in other scripts
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    formatCurrency,
    formatPercentage,
    formatDate,
    showToast,
    updateBotStatus,
    closePosition,
    handleApiError,
  };
}
