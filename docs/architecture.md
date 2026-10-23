# Architecture Documentation

This document describes the architectural layer of the SmartReceipt application. 

## SmartReceipt Application Architecture

The application follows a clean layered separation of concerns:

```text
User
  ↓
Gradio UI (app/ui.py)
  ↓
AI Service (src/services/ai_service.py)
  │
  ├── Multimodal Vision (src/capabilities/multimodal.py)
  │    ↓
  │   Model Client (src/models/model_client.py)
  │    ↓
  │   Ollama (Local Inference Server)
  │    ↓
  │   Local Model (Minicpm-v)
  │
  └── Memory / Persistent State (src/capabilities/memory.py)
       ↓
      SQLite Database (receipts.db)
```

### Core Design Rules

1. **Strict UI Isolation:** The Gradio user interface (`app/ui.py`) MUST NOT directly instantiate `OllamaModelClient` or make direct API calls to Ollama. It delegates all operations to `generate_receipt_response()` in `src/services/ai_service.py`.
2. **Controlled Failure Handling:** The model client handles low-level runtime exceptions (e.g., connection errors or missing models). The service layer converts technical exceptions into structured, user-understandable responses.
3. **Data Schemas:** Request inputs and response structures are validated using Pydantic models in `src/schemas/responses.py`.

### Core Design

1. **Gradio UI (app/ui.py):** User interface lets user upload receipts, give additional directions, view summary of the total amount spent and separate categories. User can also browse all the uploaded receipts.
2. **AI Service:** The core of the app. Catches errors and sends an error message to the user. When a receipt is uploaded, it uses 'generate_receipt_response()' to analyze the image and additional directions (and 'generate_response()' for text messages). If the analysis succeeds, it sends the data to the memory module to be saved to the database.
3. **Model Client:** Connects to the local Ollama instance via the official client, verifies model presence and checks connection drops or missing model.
4. **Multimodal:** Prompts rules and instructions to the model. The rules guide the model to find the store name, total amount, currency and date and also helps the model to separate actual items from payment methods etc. Prompt also has categories and instructions how to categorize the items and what to return. Handles the uploaded image and sends it to the vision model (minicpm-v). Parses the model output into a validated Pydantic model (ReceiptData).
5. **Memory:** Manages the local SQLite database. Prevents uploading duplicate receipts and also calculates the spending total and category percentages for the summary page.
---
