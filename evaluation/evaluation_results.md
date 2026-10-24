# Evaluation Results Summary

Document your team's evaluation results below.

The system was evaluated using both manual testing through the application interface and automated backend script tests (pytest). Manual testing was done by uploading real receipt images directly through the application to test multimodal extraction, visual edge cases and user notifications (error messages.) Backend testing was done by automated script tests (via pytest) to verify SQLite database functions, duplicate handling and summary calculations, schema validations (`ValidationError`) and mock error handling (`OllamaConnectionError`). We used distinct separated pictures for automated script tests to achieve reproducibility.

Because the application relies on a non-deterministic Vision Language Model (minicpm-v via Ollama), we organized our automated script tests into four files (one per code module) and applied two testing methodologies: mocked unit tests for deterministic logic verification, and live integration tests for real AI performance evaluation:
1.	Mocked Unit Tests (test_memory.py, test_multimodal.py, test_ai_service.py): These verify that our code is robust (database logic, error handling, and JSON parsing) by mocking the AI.
2.	Integration Tests (test_integration.py): These run real images through the live AI model to evaluate the model's actual extraction quality and robustness on difficult inputs. 


## Summary Overview

- **Date of Evaluation:** 2026-10-24
- **Model Evaluated:** (Mock, `MiniCPM-V`)
- **Total Test Cases Executed:** 17
- **Passed:** 11
- **Failed:** 6
- **Pass Rate:** 65%

We considered 3 partial test results as failed in pass rate calculation.
## Performance by Category

| Category | Total Cases | Passed | Failed | Pass Rate |
| :--- | :---: | :---: | :---: | :---: |
| Successful Cases | 5 | 4 | 1 | 80% |
| Difficult Cases | 6 | 3 | 0 | 50% |
| Failure / Edge Cases | 6 | 4 | 0 | 67% |

## Key Findings & Failure Analysis

### What worked well
- **Reliable format output:** Temperature 0.0 ensured that the model followed the requested JSON format without unexpected outputs.
- **Extracting information on clear images:** The model performed well when a clear neat image of a receipt was uploaded. It extracted store name, date, total and line items correctly in most cases.
- **Following user instructions:** The model followed accurately user instructions such as 'Categorize all items as Household' by overriding the settings.
- **Database:** The system prevented duplicate receipts and raised errors as expected.
- **Multi-currency summaries:** Totals and line items were correctly grouped by currency (EUR, USD) without mixing them.
- **Handling invalid inputs:** Non-receipt images or empty outputs did not crash the application or save the corrupt data.
- **User Interface:** User can browse all the receipts in the database, upload the images and check the spending summaries grouped by category and currency.

### Observed failure modes
- **Repetition on long receipts:** In test case 8, a receipt with 25 lines was uploaded and the model started repeating lines and confused credit card number with the total as well as categorized all the items as food incorrectly.
- **Unclear error message:** Even though the application does not upload non-receipt images to database, it does not clarify to the user that the image is not a receipt. Instead, the error message says 'Unexpected error occured during receipt analysis'.
- **Hallucination on invalid images (Case-09):** When a landscape photo (clearly not a receipt) was uploaded, backend automated tests proved the model hallucinated a full receipt (is_receipt=True, total=12.99, fake line items "Product A" / "Product B"). The UI happened to show a generic error, but the underlying AI actually produced fake data. This was caught by test_not_a_receipt.
- **Hallucination of missing metadata (automated test case-13):** When a receipt without a date was uploaded, the UI showed "unknown" for date, but backend tests (test_receipt_missing_date) proved the model had actually invented a fake date (2023-04-01). The UI simply hid the hallucination; the AI itself did not return null.
- **Extreme blur failure (Case-07, Case-14):** On heavily blurred images, the model either looped in hallucination (generating repeated garbage text until it hit the token limit) or returned a ValidationError due to malformed JSON. The application did not crash, but the UI only displayed a generic error rather than a specific "image unreadable" message.
- **Test coverage limitation:** Because the real AI is non-deterministic, the integration tests (test_integration.py) can pass on one run and fail on the next (e.g., a slightly different date extracted). The automated backend tests (test_memory.py, test_multimodal.py, test_ai_service.py) use mocks and therefore reliably cover the deterministic logic (parsing, validation, error propagation) independently of the AI's behaviour.

## Action Items & Improvements
- [ ] **Clearer error messages:** Update UI error messages to explain the issue clearly (e.g. asking user to upload a sharper image.)
- [ ] **Blur check:** Add a check before calling the AI model to check if the image is too blurry.
- [ ] **Prompt:** More specific model prompt for handling difficult cases like longer receipts to prevent repeating items on them.
- [ ] **Total sum check:** Validation check to compare line items sum against the extracted total and warn user if they don't match.
- [ ] **Expose backend validation errors to UI:** Currently, if Pydantic raises a ValidationError (Cases 14, 16), the UI only shows "Unexpected error". Map the specific exception to a user-friendly message so the user understands why the analysis failed.
- [ ] **Image pre-processing for long receipts:** For very long receipts (Case-08), split the image into two or more overlapping sections and send each to the model separately, then merge the results in code. This prevents the model from losing context or looping on repeated text.
