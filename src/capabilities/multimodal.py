"""
Optional project capability: Multimodal Interaction.

Implement this module only if this capability is relevant to your application's
user problem. Remove the file if the capability is not used.

Conceptual Overview:
-------------------
Multimodal interaction enables applications to combine text inputs with images or other non-text
modalities when querying vision-capable models.

Key concepts when implementing multimodal features:
1. Input Handling: Accepting image files alongside text prompts in the user interface.
2. Image Processing & Encoding: Converting images to base64 encoding or passing image paths
   to compatible local vision models (e.g., llava, llama3.2-vision).
3. Service Integration: Extending the application service layer to accept multimodal payloads.

Note:
-----
Verify that your local Ollama model explicitly supports multimodal inputs before testing.
"""

# Implement custom multimodal handling below if selected.

from src.models.model_client import OllamaModelClient
from src.schemas.responses import ReceiptData
from typing import Optional


def analyze_receipt(image_path: str, client: OllamaModelClient, user_instructions: Optional[str] = None):
    """Analyzes a receipt image and identifies products, prices and categories."""

    prompt = """
        Analyze this picture of a receipt.

        Identify the purchased products, their prices and categories.

        Rules:
        - Store: Always extract the store name from the very top line of the receipt. It is usually the largest text, company name or brand banner
        (e.g. "Sephora", "Walmart", "Prisma", "Lidl", "Rolex"). Read the exact name on top of the receipt but DO NOT use street address, business ID (Y-tunnus)
        or website URL. Only use "Unknown" if the top part is completely cut off or blacked out.
        - Currency: Identify the currency code (EUR, USD, GBP, SEK). Check symbols: '$' = USD, '€' = EUR, '£' = GBP, 'kr' = SEK. If the receipt has a US address/state (e.g. NY, OH) or mentions US DEBIT, use USD.
        - Date: Look for dates in any format like MM-DD-YYYY, DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, or DD.MM.YYYY. Always convert and return it in format: YYYY-MM-DD. If completely unreadable, return null.
        - Total: Look for the final payable amount explicitly labeled as 'TOTAL', 'SUMMA', or 'YHTEENSÄ'. DO NOT extract card numbers (such as debit card endings like 9166), SUBTOTAL, TAX, or change (CHANGE DUE) as the total.
        - Items: Include ONLY actual purchased products. Do not include payment methods like Mastercard, Visa, US Debit and Amex. Do not include VAT, ALV and TAX.
        Do not include coupons.

        Use these product categories:
        - Food
        - Clothing
        - Hygiene
        - Restaurant
        - Household
        - Other

        Instructions:
        - If the receipt is from a grocery store or supermarket,
          classify food products as Food.
        - If the receipt is from a restaurant, cafe or fast-food restaurant,
          classify the purchases as Restaurant, not Food.
        - If the receipt is from a clothing store, classify purchases as Clothing.
        - If the receipt contains hygiene or beauty products,
          classify them as Hygiene.
        - If the receipt contains cleaning or household products,
          classify them as Household.
        - If a product does not fit any other category, classify it as Other.
        - If a product or price is unclear, state that it is unclear
          instead of guessing.

        Return:
        - Store (The merchant name from the top header)
        - Date
        - Currency
        - The category of each product
        - A list of products and their prices
        - The total amount
        """
    if user_instructions and user_instructions.strip():
        prompt += f"\n\nAdditional User Instructions:\n{user_instructions.strip()}"

    raw_text = client.generate_from_image(
        prompt = prompt,
        image_path = str(image_path),
        schema = ReceiptData.model_json_schema(),
    )

    receipt = ReceiptData.model_validate_json(raw_text)

    return receipt, raw_text