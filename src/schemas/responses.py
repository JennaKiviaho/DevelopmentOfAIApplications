from pydantic import BaseModel, Field
from typing import Annotated, Literal
from datetime import date
from decimal import Decimal
from typing import Optional

NonBlank = Annotated[str, Field(min_length=1, max_length=500)]
Money = Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=2, allow_inf_nan=False)]
CategoryType = Literal["Food", "Clothing", "Hygiene", "Restaurant", "Household", "Other"]

class UserRequest(BaseModel):
    """Minimal schema for validating incoming user input."""

    message: str = Field(..., description="The user's prompt or message.")


class AIResponse(BaseModel):
    """Minimal schema for structured response output from the AI service layer."""

    content: str = Field(..., description="The generated response text or user-friendly error message.")
    success: bool = Field(True, description="Flag indicating if the operation succeeded.")
    error_message: str | None = Field(None, description="Detailed error description if success is False.")

class ReceiptLineItem(BaseModel):
    name: NonBlank = Field(description="Product name")
    price: Money = Field(description="Product price")
    category: CategoryType = Field(description="Product category")

class ReceiptData(BaseModel):
    is_receipt: bool = Field(description="true if receipt, false if something else like animal or landscape")
    store: NonBlank = Field(default="Unknown", description = "Store or restaurant name")
    date: Optional[str] = Field(default=None, description="Receipts date YYYY-MM-DD")
    total: Money = Field(description="Receipts total sum")
    currency: Literal["EUR", "USD", "GBP", "SEK"] = Field(default="EUR", description="Currency code like EUR, USD, GBP, SEK")
    items: list[ReceiptLineItem] = Field(default_factory=list, max_length=500)