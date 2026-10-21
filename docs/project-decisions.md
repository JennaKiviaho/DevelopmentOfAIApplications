# Project decisions

Use this decision log to document significant technical and architectural choices made by your team during development.

## Decision 1 — Model selection

**Decision:**
We decided to use the vision-capable model MiniCPM-V for our receipt analysis model.

**Alternatives considered:**
After studying the MiniCPM-V we did not even consider other models. The choice was easily made.

**Why we chose this:**
Our application analyzes receipts and categorizes the purchases, so that the user is able to track their spending more easily. We needed a model that understands both text and image layout. The model can extract store names, dates, purchased items, prices from the image in one workflow. Using Ollama we are able to run the AI model locally without any external API.
---

## Decision 2 — Additional AI capability

**Decision:**
Using the multimodal AI to analyze the receipts.

**Why it is needed:**
The input is a photograph of the receipt or a scanned version and not a text prompt. The app sends the image and extraction instructions to the model, requests a response following the ReceiptData JSON schema and validates the returned JSON using Pydantic.

**Alternatives considered:**
Well this could have been done manually for example by applying OCR first and then sending the text to a text-only model and then creating separate classification rules without the vision model. Multimodal processing however, simplifies the user workflow.
---

## Decision 3 — Architecture

**Decision:**
Separating the Gradio user interface, application service, model client, data schemas and the capability models.

**Why:**
Separating the app into different files keeps the project organized and makes it easier to understand. It is easier to make small changes to the code.

For example:

- ui.py handles the user interface.

- ai_service.py handles the main application logic.

- multimodal.py handles receipt analysis.

- model_client.py communicates with Ollama.

- memory.py handles the database.

- responses.py contains the data models.

## Decision 4 - Database

**Decision:**
Store receipts and their line items in SQLite using src/capabilities/memory.py.

**Why:**
SQLite is simple to use with Python and does not need a separate database server. The app saves the receipt information and purchased items into the database. We also added a check up to prevent the same receipt from being saved twice. For example two different receipts with the same store, date and total price are considered as duplicates.



