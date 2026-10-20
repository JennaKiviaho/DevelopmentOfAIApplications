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
    
def navigate(page):
    """Show the selected application page."""
    return (
        gr.update(visible=page == "home"),
        gr.update(visible=page == "upload"),
        gr.update(visible=page == "receipts"),
        gr.update(visible=page == "summary"),
    )

def build_ui() -> gr.Blocks:
    """Build the SmartReceipt application interface."""

    with gr.Blocks(
        title="SmartReceipt"
    ) as demo:

        # Home page
        with gr.Column(visible=True) as home_page:

            gr.HTML("""
                <div class="hero">
                    <h1>SmartReceipt</h1>
                    <p>Your receipts, simplified.</p>
                    <p>
                        Track purchases, organize receipts
                        and understand your spending.
                    </p>
                </div>
            """)

            gr.Markdown("## What would you like to do?")

            with gr.Row():
                upload_nav = gr.Button("Upload Receipt",elem_classes=["dashboard-button"])
                receipts_nav = gr.Button("My Receipts",elem_classes=["dashboard-button"])
                summary_nav = gr.Button("Spending Summary",elem_classes=["dashboard-button"])

        # Upload Receipt - page
        with gr.Column(visible=False) as upload_page:

            upload_back = gr.Button("Back to Home",elem_classes=["back-button"])

            gr.Markdown("## Upload Receipt")
            gr.Markdown("Upload your receipt to analyze your purchases.")

            receipt_image = gr.Image(label="Receipt Image",type="filepath",elem_id="receipt-upload")

            analyze_button = gr.Button("Analyze Receipt",variant="primary", elem_classes=["action-button"])

            with gr.Row():
                cancel_upload_button = gr.Button("Cancel Upload")
                cancel_analysis_button = gr.Button("Cancel Analysis")

            receipt_output = gr.Textbox(label="Analysis Result",lines=12,interactive=False,elem_id="receipt-analysis")

            analyze_event = analyze_button.click(fn=analyze_receipt,inputs=receipt_image,outputs=receipt_output)

            cancel_upload_button.click(fn=lambda: (None, ""),inputs=None,outputs=[receipt_image, receipt_output])
            cancel_analysis_button.click(fn=lambda: "Analysis cancelled.",inputs=None,outputs=receipt_output,cancels=[analyze_event])

        # My Receipts - page
        with gr.Column(visible=False) as receipts_page:

            receipts_back = gr.Button("Back to Home",elem_classes=["back-button"])

            gr.Markdown("## My Receipts")
            gr.Markdown("View your saved receipts.")

            refresh_button = gr.Button("Refresh Receipts",elem_classes=["action-button"])

            receipts_table = gr.Dataframe(
                headers=["ID","Store","Date","Total","Currency","Created At"],label="Saved Receipts",interactive=False,)

            refresh_button.click(fn=refresh_receipts,inputs=None,outputs=receipts_table)

        # Spending Summary - page
        with gr.Column(visible=False) as summary_page:

            summary_back = gr.Button("Back to Home",elem_classes=["back-button"])

            gr.Markdown("## Spending Summary")
            gr.Markdown("Review your spending by product category.")

            summary_button = gr.Button("Update Summary",variant="primary",elem_classes=["action-button"])
            summary_output = gr.Markdown()

            category_table = gr.Dataframe(
                headers=["Category","Amount","Percentage"],label="Spending by Category",interactive=False)

            summary_button.click(fn=format_summary,inputs=None,outputs=[summary_output, category_table])

        # Navigation
        pages = [home_page,upload_page,receipts_page,summary_page]

        upload_nav.click(fn=lambda: navigate("upload"),outputs=pages)
        receipts_nav.click(fn=lambda: navigate("receipts"),outputs=pages).then(fn=refresh_receipts,outputs=receipts_table)
        summary_nav.click(fn=lambda: navigate("summary"),outputs=pages).then(fn=format_summary,outputs=[summary_output, category_table])

        for back_button in [upload_back,receipts_back,summary_back]:
            back_button.click(fn=lambda: navigate("home"),outputs=pages)

        # Load the current database information when the app opens.
        demo.load(fn=refresh_receipts,inputs=None,outputs=receipts_table,)
        demo.load(fn=format_summary,inputs=None,outputs=[summary_output,category_table,])

    return demo
