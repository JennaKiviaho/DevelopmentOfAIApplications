import gradio as gr
from src.services.ai_service import generate_response, generate_receipt_response
from src.capabilities.memory import list_receipts, get_summary

def analyze_receipt(image_path):
    """Analyze an uploaded receipt image."""
    if image_path is None:
        return "Please upload a receipt first."
    result = generate_receipt_response(image_path)
    return result.content

def refresh_receipts():
    """Return saved receipts for display."""
    try:
        return list_receipts()
    except Exception as err:
        print(f"Could not load receipts: {err}")
        return []

def format_summary():
    """Create a readable spending summary and category table."""
    try:
        summary = get_summary()

        total = summary["total_spending"]
        currency = summary["currency"]
        receipt_count = summary["receipt_count"]

        text = (
            "## Spending Overview\n\n"
            f"**Total spending:** {total:.2f} {currency}\n\n"
            f"**Saved receipts:** {receipt_count}\n\n"
            "### Spending by category\n"
        )

        categories = []

        for item in summary["categories"]:
            categories.append([
                item["category"],
                f'{item["total"]:.2f} {currency}',
                f'{item["percentage"]}%'
            ])

        if not categories:
            text += "\nNo purchases have been saved yet."

        return text, categories

    except Exception as err:
        print(f"Could not create spending summary: {err}")
        return ("Could not load the spending summary.",[])

def build_ui() -> gr.Blocks:
    """ Build the SmartReceipt application interface. """
    with gr.Blocks(title="SmartReceipt") as demo:
        gr.Markdown(
            """
            # SmartReceipt
            
            Upload your receipts, automatically categorize your purchases and understand where your money goes.
            Your purchases are analyzed by AI and stored locally in the application's database.
            """
        )

        with gr.Tab("Upload Receipt"):

            gr.Markdown("Upload your receipt to analyze the contents.")
            receipt_image = gr.Image(label="Receipt Image", type="filepath")
            analyze_button = gr.Button("Analyze Receipt",variant="primary")
            receipt_output = gr.Textbox(label="Analysis Result", lines=12, interactive=False)
            analyze_button.click(fn=analyze_receipt, inputs=receipt_image, outputs=receipt_output)

        with gr.Tab("My Receipts"):

            gr.Markdown("View receipts saved in the database.")
            refresh_button = gr.Button("Refresh Receipts")
            receipts_table = gr.Dataframe(headers=["ID","Store","Date","Total","Currency","Created At"],label="Saved Receipts",interactive=False)
            refresh_button.click(fn=refresh_receipts,inputs=None,outputs=receipts_table)

        with gr.Tab("Spending Summary"):

            gr.Markdown("Review your spending by product category.")

            summary_button = gr.Button("Update Summary",variant="primary")
            summary_output = gr.Markdown()
            category_table = gr.Dataframe(headers=["Category","Amount","Percentage"],label="Spending by Category",interactive=False)
            summary_button.click(fn=format_summary,inputs=None,outputs=[summary_output,category_table,])

        # Load the current database information when the app opens.
        demo.load(fn=refresh_receipts,inputs=None,outputs=receipts_table,)
        demo.load(fn=format_summary,inputs=None,outputs=[summary_output,category_table,])

    return demo
