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
        - Store: Read the business/store name from the top header or logo area (e.g. "Green Supermarket"). Look for title text. If partially obscured, infer the best match. Do not return "Unknown" if readable text exists at the top.
        - Currency: Check for currency signs (€, EUR, $, £, kr). Default is 'EUR'.
        - Date: Look for dates in any format like MM-DD-YYYY, DD/MM/YYYY, YYYY-MM-DD, or DD.MM.YYYY. Always convert and return it in format: YYYY-MM-DD. If completely unreadable, return null.
        - Total: Look for a total amount at the bottom. If no total sum is explicitly printed, sum up all the prices and return that value. Do not return 0.00 if there are items.
        - Items: Include only actual purchased products. Do not include payment methods like Mastercard and Visa or VAT and ALV.

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