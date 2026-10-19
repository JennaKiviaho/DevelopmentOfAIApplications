from typing import Optional

from src.models.model_client import (
    OllamaModelClient,
    ModelClientError,
    OllamaConnectionError,
    ModelNotFoundError,
)
from src.schemas.responses import UserRequest, AIResponse, ReceiptData
from src.capabilities.memory import save_receipt, DuplicateReceiptError


class AIService:
    """
    Application service layer responsible for validating user input,
    orchestrating model client requests, and catching exceptions gracefully.
    """

    def __init__(self, model_client: Optional[OllamaModelClient] = None):
        # Allow injecting custom/mock model_client for simple testing
        self.model_client = model_client

    def _get_client(self) -> OllamaModelClient:
        """Returns active model client, initializing default client if none provided."""
        if self.model_client is None:
            self.model_client = OllamaModelClient()
        return self.model_client

    def process_message(self, user_message: str) -> AIResponse:
        """
        Processes a raw user message string and returns a structured AIResponse.
        Catches technical failures and converts them to friendly user-facing messages.
        """

        # Validate empty input
        if not user_message or not user_message.strip():
            return AIResponse(
                content="Please enter a message before sending.",
                success=False,
                error_message="User message was empty.",
            )

        try:
            # Validate the input using the request schema
            request = UserRequest(message=user_message.strip())

            # Send the message to the AI model
            client = self._get_client()
            response_text = client.generate(request.message)

            return AIResponse(
                content=response_text,
                success=True,
            )

        except OllamaConnectionError as err:
            return AIResponse(
                content=(
                    "[Error] Could not connect to Ollama.\n\n"
                    "Please verify that Ollama is installed and running locally on your machine."
                ),
                success=False,
                error_message=str(err),
            )

        except ModelNotFoundError as err:
            return AIResponse(
                content=(
                    "[Error] The configured AI model is unavailable in Ollama.\n\n"
                    "Please verify your MODEL_NAME setting or run "
                    "'ollama run <model_name>'."
                ),
                success=False,
                error_message=str(err),
            )

        except ModelClientError as err:
            return AIResponse(
                content=(
                    "[Error] An unexpected communication error occurred "
                    "with the AI model."
                ),
                success=False,
                error_message=str(err),
            )

        except Exception as err:
            return AIResponse(
                content="[Error] An unexpected application error occurred.",
                success=False,
                error_message=str(err),
            )

    def process_receipt(self, image_path: str) -> AIResponse:
        """Analyzes a receipt image and identifies products, prices and categories."""

        if not image_path or not image_path.strip():
            return AIResponse(
                content="Please upload your receipt.",
                success=False,
                error_message="No receipt was found. Try again.",
            )

        prompt = """
        Analyze this picture of a receipt.

        Identify the purchased products, their prices and categories.

        Rules:
        - Store: Look at the top of the receipt for the store name.
        - Currency: Default is 'EUR' unless there is clearly 'USD', 'GBD' or 'SEK'.
        - Date: Return in format YYYY-MM-DD if visible, otherwise NULL.
        - Total: Look for a total amount at the bottom. If no total sum is explicitly printed, sum up all the prices and return that value. Do not return 0.00 if there are items.

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

        try:
            client = self._get_client()

            response = client._client.chat(
                model = client.model_name,
                messages = [{"role": "user",
                           "content": prompt,
                           "images": [str(image_path)]
                           }],
                format = ReceiptData.model_json_schema(),
                options = {"temperature": 0.0},
                stream = False,
            )

            raw_text = response.get("message", {}).get("content", "{}")
            receipt = ReceiptData.model_validate_json(raw_text)

            if not receipt.is_receipt:
                return AIResponse(
                    content="Image is not receipt. Upload a clear image of a receipt.",
                    success=False,
                    error_message = "Image is not a receipt."
                )

            try:
                receipt_id = save_receipt(
                    receipt = receipt,
                    source_filename = str(image_path),
                    raw_text = raw_text,
                )
                status = f"Receipt uploaded to database (ID: {receipt_id})."
            except DuplicateReceiptError as e:
                status = f"{e}"

            item_lines = "\n".join([f"- {item.name}: {item.price} {receipt.currency} ({item.category})" for item in receipt.items])

            content = (
                f"{status}\n\n"
                f"Store: {receipt.store}\n"
                f"Date: {receipt.date or 'Unknown'}\n"
                f"Total: {receipt.total} {receipt.currency}\n\n"
                f"Items: \n{item_lines}"
            )

            return AIResponse(
                content = content,
                success = True,
            )

        except OllamaConnectionError as err:
            return AIResponse(
                content=(
                    "Could not connect to Ollama. "
                    "Please check that it is running."
                ),
                success=False,
                error_message=str(err),
            )

        except ModelNotFoundError as err:
            return AIResponse(
                content="The configured AI model was not found in Ollama.",
                success=False,
                error_message=str(err),
            )

        except ModelClientError as err:
            return AIResponse(
                content="An error occurred while analyzing the receipt.",
                success=False,
                error_message=str(err),
            )

        except Exception as err:
            return AIResponse(
                content="An unexpected error occurred during receipt analysis.",
                success=False,
                error_message=str(err),
            )


def generate_response(
    user_message: str,
    service: Optional[AIService] = None,
) -> str:
    """
    Main reusable service entry point used by the UI layer.

    Accepts user input, passes it to the AI service, and returns
    the generated text response or a friendly error message.
    """

    active_service = service or AIService()
    response = active_service.process_message(user_message)

    return response.content


def generate_receipt_response(
    image_path: str,
    service: Optional[AIService] = None,
) -> AIResponse:
    """Entry point for processing receipt images from the UI."""

    active_service = service or AIService()
    return active_service.process_receipt(image_path)