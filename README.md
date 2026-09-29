# Project name

Starter template for the **Development of AI Applications** course final group project.

## Team members

- Lotta Kauppinen (amk1005174@student.hamk.fi / lotta.kauppinen@student.hamk.fi)
- Jenna Kiviaho (amk1004342@student.hamk.fi)
- Marjaana Koski (email@example.com)
- Jani Laakso (email@example.com)

## Problem

### Intended users

- The target user is someone who wants to track their everyday spending easily. 
- The app is useful for someone who makes purchases in store or online and are able to get a receipt from the purchase. 

### Problem statement

Going through receipts and tracking personal spending can be time-consuming because products are not automatically categorized. Users must manually identify and categorize their purchases to understand which types of products they buy most frequently and which categories consume the largest portion of their budget.

This manual process makes it difficult to maintain an up-to-date overview of personal spending. The application addresses this problem by automatically extracting and categorizing purchases from receipts, allowing users to more easily understand their spending habits.

### Why AI is appropriate

Receipts can vary in layout, wording, product names or the level of detail. A more traditional system based on rules, would require many predefined rules. An AI model can easily understand different formats or wording that varies between receipts.

## Solution

The application is a personal spending tracker that allows users to submit the receipts of their recent purchases. It uses AI to extract the products, prices and other relevant information. After that it will categorize the purchases into different spending categories such as groceries, entertainment, restaurants, hygienic products, clothing etc. 

The application reduces the manual work that goes into categorizing the purchases and tracking on what takes the largest portion of the budget. The user receives a structured data of their spending habits.

## Main user workflow

1. **User Input:** The user uploads a receipt through the Gradio user interface.
2. **Processing & Guardrails:** The application service layer (`src/services/ai_service.py`) validates and formats the request.
3. **Model Response:** The model client calls Ollama locally and returns the response back through the service layer to the UI.

## Architecture

Below is the initial starter architecture. As your project evolves with additional capabilities, replace or extend this diagram in [`docs/architecture.md`](docs/architecture.md).

```text
User
  ↓
Gradio UI (app/ui.py)
  ↓
Application / AI Service (src/services/ai_service.py)
  ↓
Model Client (src/models/model_client.py)
  ↓
Ollama (Local LLM Server)
```

> **Core Architectural Rule:** The user interface must NEVER communicate directly with the model client or Ollama. All interactions must pass through the service layer (`ai_service.py`).

## Model

- **Model used:** `minicpm-v`
- **Selection rationale:**
  - **Accessibility:** The llama3.2-vision is restricted in EU unlike minicpm-v is available globally and locally via Ollama.
  - **Performance:** Processes both image and text input and it has a strong OCR capability. Model can categorize items into to structured format (JSON).
  - **Hardware efficiency:** Model is lightweight and does run well with standard hardware.
  - **Capability:** Reads small and dense text efficiently by dividing images to pieces.

## Additional AI capability

Select at least one additional capability to implement for your final project:

- [ ] RAG (Retrieval-Augmented Generation)
- [ ] Tools / External API integration
- [ ] Model Context Protocol (MCP)
- [ ] Agentic workflow (Model-selected actions based on observations)
- [x] Memory / Persistent state
- [x] Multimodal interaction (Text + Images)
- [ ] Other: ______________________

### Capability justification
Explain why the selected capability is useful and necessary for your application's user problem.

- **Multimodal interaction:**:
  Receipts can be photos or digital images. A multimodal model can read the receipt image and user's given instructions at the same time.

- **Memory / Persistent state:**
  The app tracks spending so it needs to remember past purchases. The data of the receipts are saved and the user is able to see total spending and summaries over time.

## Setup

### 1. Create the Conda environment

```bash
conda env create -f environment.yml
```

### 2. Activate the environment

```bash
conda activate dev-ai-project
```

### 3. Configure environment variables

Copy `.env.example` to create your local `.env` configuration file:

On Linux / macOS:
```bash
cp .env.example .env
```

On Windows (Command Prompt / PowerShell):
```powershell
copy .env.example .env
```

Ensure `.env` contains valid values for `OLLAMA_BASE_URL` and `MODEL_NAME`:
```env
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=minicpm-v
```

### 4. Start Ollama

Make sure Ollama is installed and running locally, then pull your configured model:

```bash
ollama run minicpm-v
```

### 5. Run the application

Run the application from the root directory of the project:

```bash
python -m app.main
```

Then open your browser at `http://localhost:7860`.

### 6. Run automated tests

```bash
pytest
```

## Evaluation

Describe your evaluation methodology and summarize key results. Starter test cases can be found in [`evaluation/test_cases.json`](evaluation/test_cases.json).

Refer to [`evaluation/README.md`](evaluation/README.md) for guidelines on defining success, edge cases, and failure scenarios.

- **Successful case:**
  Clear picture of a receipt to verify the model extracts all the items and prices correctly from the image and then categorizes products into structured format (JSON).

- **Difficult case:**
  Unclear image of a receipt, which can be for example a blurry picture or wrinkled receipt. This is to test how model handles imperfect visual quality.

- **Failure case:** Testing with a picture of something else than a receipt, for example a picture of a dog, to ensure the system sends an error message with out crashing and fabricating purchases.

## Known limitations

- Highlight known system limitations, unhandled edge cases, or boundaries of current capabilities.

- **Image quality:** 
  The images of the receipts need to be clear. Blurry or unclear images might lead to mistakes like missed items and other errors.
- **Abbreviations:**
  Some store abbreviations might be hard for the model to understand.
- **Local run:**
  Running the model locally might take a few seconds to read the image.

## Future improvements

- List planned feature enhancements, architectural refactorings, or future capabilities.

- **Monthly budget:**
  Allows to add a monthly budget and then gives user a warning when budget is about to be exceeded.

- **Editing:**
  If AI makes a mistake with pricing, item name or category, manual editing could be useful to fix these mistakes by hand.
