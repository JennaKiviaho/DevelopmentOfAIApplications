# Evaluation Results Summary

Document your team's evaluation results below.

The system was evaluated using both manual testing through the application interface and automated backend tests (pytest). Manual testing was done by uploading real receipt images directly through the application to test multimodal extraction, visual edge cases and user notifications (error messages.) Backend testing was done to verify SQLite database functions, duplicate handling and summary calculations, schema validations (`ValidationError`) and mock error handling (`OllamaConnectionError`).

## Summary Overview

- **Date of Evaluation:** YYYY-MM-DD
- **Model Evaluated:** (e.g., `MiniCPM-V`)
- **Total Test Cases Executed:** 0
- **Passed:** 0
- **Failed:** 0
- **Pass Rate:** 0%

## Performance by Category

| Category | Total Cases | Passed | Failed | Pass Rate |
| :--- | :---: | :---: | :---: | :---: |
| Successful Cases | 0 | 0 | 0 | 0% |
| Difficult Cases | 0 | 0 | 0 | 0% |
| Failure / Edge Cases | 0 | 0 | 0 | 0% |

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

## Action Items & Improvements
- [ ] **Clearer error messages:** Update UI error messages to explain the issue clearly (e.g. asking user to upload a sharper image.)
- [ ] **Blur check:** Add a check before calling the AI model to check if the image is too blurry.
- [ ] **Prompt:** More specific model prompt for handling difficult cases like longer receipts to prevent repeating items on them.
- [ ] **Total sum check:** Validation check to compare line items sum against the extracted total and warn user if they don't match.
