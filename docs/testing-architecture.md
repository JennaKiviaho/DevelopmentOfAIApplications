# Testing Architecture Documentation

This document describes the testing architecture of the SmartReceipt application. 

## SmartReceipt Testing Architecture

The test suite follows a clean layered separation of concerns, mirroring the application architecture:

```text
Test Runner (pytest)
  ↓
pytest.ini (marker configuration)
  ↓
tests/
  │
  ├── test_multimodal.py   ← Mocks Model Client → verifies parsing & JSON schema
  ├── test_memory.py       ← Uses temp SQLite DB → verifies persistence & aggregation
  ├── test_ai_service.py   ← Mocks Model Client → verifies service errors & validation
  └── test_integration.py  ← Real Ollama + real images → verifies model behavior

```

### Core Testing Rules

**Mocked unit tests never touch the real AI.** Files test_multimodal.py and test_ai_service.py replace OllamaModelClient with a MagicMock. This guarantees deterministic, fast execution (under 1 second) and isolates our parsing/error-handling logic from the AI's non-determinism.

**Database tests never touch the production database.** test_memory.py uses pytest's built-in tmp_path fixture to create an isolated SQLite file per test. The real receipts.db is never modified during testing.

**Integration tests are opt-in.** Files using a live model are tagged with @pytest.mark.integration. This allows CI pipelines and quick local runs to execute the fast suite via pytest -m "not integration" without waiting for the slow AI.

**Assertions are property-based in integration tests.** Because AI output varies across runs, integration tests assert on properties (e.g., store is not None, len(items) > 0) rather than exact values. Exact-value assertions are reserved for mocked tests where the input is controlled.

### Test File Breakdown

test_multimodal.py (Mocked Unit Tests)
Tests analyze_receipt() in src/capabilities/multimodal.py. Replaces the model client with a mock returning controlled JSON strings. Verifies that valid AI responses are parsed into a correct ReceiptData object (all fields extracted), and that invalid responses (malformed JSON, missing required fields) raise a ValidationError. Also verifies that OllamaConnectionError propagates cleanly from the client.

test_memory.py (Database Unit Tests)
Tests save_receipt(), list_receipts(), and get_summary() in src/capabilities/memory.py. Each test uses a fresh temporary SQLite database, so no test interferes with another. Verifies line-item persistence, duplicate rejection, date filtering, listing, and multi-currency summary aggregation.

test_ai_service.py (Service Layer Tests)
Tests AIService.process_message() and generate_response() in src/services/ai_service.py. Uses a mocked model client to verify the service layer's role: rejecting empty inputs before the AI is called, formatting successful responses, and catching low-level exceptions (OllamaConnectionError, ModelNotFoundError) and converting them into user-friendly error messages.

test_integration.py (Live Integration Tests)
Tests the full image-analysis pipeline against the real minicpm-v model via Ollama, using real fixture images under tests/fixtures/. Evaluates how the AI handles wrinkled, blurred, long, and non-receipt images, as well as custom user instructions. Assertions are property-based (e.g., "date should be present") because the same image may yield slightly different output on different runs.

### Design Filosophy
The test suite is intentionally split across four files because each file tests a different layer of the application with a different testing strategy. Collapsing them into one file would either force all tests to be slow (if integration tests dominate) or force the AI-dependent tests to become meaningless (if mocks dominate). Separating them allows fast, deterministic coverage of the application logic, alongside slower, real-world evaluation of the AI model's behavior.

Mocks are used whenever the code is the subject of the test; the real model is used whenever the model's quality is the subject. This distinction is what makes the suite both reliable (in CI) and meaningful (in evaluation).
