# Stock Trading Bot Documentation

Welcome to the documentation for the AI Stock Trading Bot.

## 📚 Documentation Index

### Quick Start

- **[Setup Guide](setup/STARTUP.md)** - Complete installation and setup instructions
- **[Main README](../README.md)** - Project overview and quick reference

### Testing

- **[Integration Test Results](testing/INTEGRATION_TEST_RESULTS.md)** - Results from Tests 1-13
- **[Test 14 Startup Guide](testing/TEST_14_STARTUP_GUIDE.md)** - Step-by-step guide for 48-hour stability test
- **[Test 14 Checklist](testing/TEST_14_CHECKLIST.md)** - Comprehensive verification checklist
- **[Test 14 Validation Report](testing/TEST_14_VALIDATION_REPORT.md)** - Test 14 results and analysis

### Planning & Architecture

- **[Implementation Plan](planning/implementation_plan.md)** - React Dashboard migration plan (Phase 11)
- **[ML Accuracy Improvement Plan](planning/ml_accuracy_improvement_plan.md)** - Machine learning optimization strategies

### API Documentation

- **[API Reference](api/README.md)** - _To be created in Phase 10_
  - Flask API endpoints (18 total)
  - Request/response schemas
  - Authentication and error handling

### Dashboard Documentation

See **[dashboard/docs/](../dashboard/docs/)** for React dashboard-specific documentation:

- API Test Guide
- Phase completion reports
- Component architecture

### Memory Bank

Project context, patterns, and progress tracking:

- **[memory-bank/](../memory-bank/)** - Complete project context
  - `projectbrief.md` - Core requirements and goals
  - `productContext.md` - Product vision and UX goals
  - `activeContext.md` - Current status and recent work
  - `systemPatterns.md` - Architecture and design patterns
  - `techContext.md` - Technology stack and setup
  - `progress.md` - Detailed progress tracking

---

## 🏗️ Project Structure

```
stock-bot/
├── src/              # Source code (14 Python modules)
├── tests/            # Organized test suite (unit/integration/e2e)
├── scripts/          # Startup and utility scripts
├── docs/             # This documentation (you are here)
├── config/           # Configuration files
├── logs/             # Runtime logs
├── models/           # ML models (LSTM, Random Forest)
├── memory-bank/      # Project Memory Bank
└── dashboard/        # React TypeScript frontend
```

---

## 🚀 Quick Links

**Running the Bot:**

```bash
# From project root
python src/main.py

# Or use startup scripts
cd scripts
./start-bot.sh    # Linux/Mac
start-bot.bat     # Windows
```

**Running Tests:**

```bash
# All tests
pytest

# Specific test type
pytest tests/unit/          # Fast unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/           # End-to-end tests

# With coverage
pytest --cov=src tests/
```

**Starting Dashboard:**

```bash
# Flask dashboard (port 5000)
python src/dashboard/app.py

# React dashboard (port 3000) - Phase 11
cd dashboard
npm run dev
```

---

## 📖 Documentation Conventions

- **Setup guides** → `docs/setup/`
- **Test documentation** → `docs/testing/`
- **Planning documents** → `docs/planning/`
- **API reference** → `docs/api/`
- **Dashboard docs** → `dashboard/docs/`

---

## 🤝 Contributing

When adding new documentation:

1. Place in appropriate subdirectory
2. Update this README.md index
3. Follow Markdown conventions
4. Include code examples where helpful

---

## 📝 Documentation Status

| Category        | Status      | Location           |
| --------------- | ----------- | ------------------ |
| Setup Guide     | ✅ Complete | `setup/STARTUP.md` |
| Testing Docs    | ✅ Complete | `testing/`         |
| Planning Docs   | ✅ Complete | `planning/`        |
| API Docs        | ❌ Pending  | `api/` (Phase 10)  |
| User Guide      | ❌ Pending  | To be created      |
| Troubleshooting | ❌ Pending  | To be created      |

---

**Last Updated:** November 15, 2025
