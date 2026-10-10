import io

from django.http import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor("#0B3561")
TEAL = colors.HexColor("#12A5B0")


def build_invoice_pdf(order):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("InvoiceTitle", parent=styles["Title"], textColor=NAVY, fontSize=22)
    label_style = ParagraphStyle("Label", parent=styles["Normal"], textColor=TEAL, fontSize=9, spaceAfter=2)
    normal = styles["Normal"]

    elements = [
        Paragraph(order.legal_business_name_snapshot or "PyNotes", title_style),
        Spacer(1, 2 * mm),
    ]
    if order.gstin_snapshot:
        elements.append(Paragraph(f"GSTIN: {order.gstin_snapshot}", normal))
    elements.append(Spacer(1, 6 * mm))

    meta_table = Table(
        [
            ["Invoice / Order No.", str(order.order_number)],
            ["Order date", order.created_at.strftime("%d %b %Y")],
            ["Payment method", order.get_payment_method_display()],
            ["Status", order.get_status_display()],
        ],
        colWidths=[60 * mm, 90 * mm],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), TEAL),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    elements.append(meta_table)
    elements.append(Spacer(1, 6 * mm))

    elements.append(Paragraph("BILL TO / SHIP TO", label_style))
    address_lines = [
        order.shipping_full_name,
        order.shipping_line1,
        order.shipping_line2,
        f"{order.shipping_city}, {order.shipping_state} {order.shipping_postal_code}",
        order.shipping_country,
        order.email,
    ]
    for line in filter(None, address_lines):
        elements.append(Paragraph(line, normal))
    elements.append(Spacer(1, 8 * mm))

    item_rows = [["Item", "HSN", "Qty", "Unit Price", "Amount"]]
    for item in order.items.all():
        item_rows.append(
            [
                item.product_name,
                item.hsn_code or "-",
                str(item.quantity),
                f"₹{item.unit_price}",
                f"₹{item.line_total}",
            ]
        )
    items_table = Table(item_rows, colWidths=[70 * mm, 20 * mm, 15 * mm, 30 * mm, 30 * mm])
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe5ec")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(items_table)
    elements.append(Spacer(1, 6 * mm))

    summary_rows = [["Subtotal", f"₹{order.subtotal}"]]
    if order.discount_total:
        summary_rows.append(["Coupon discount", f"-₹{order.discount_total}"])
    if order.prepaid_discount_total:
        summary_rows.append(["Prepaid discount", f"-₹{order.prepaid_discount_total}"])
    if order.cod_fee:
        summary_rows.append(["COD fee", f"₹{order.cod_fee}"])
    summary_rows.append(["Shipping", f"₹{order.shipping_cost}"])
    if order.tax_total:
        half = (order.tax_total / 2).quantize(order.tax_total)
        summary_rows.append(["CGST", f"₹{half}"])
        summary_rows.append(["SGST", f"₹{half}"])
    summary_rows.append(["Total", f"₹{order.total}"])

    summary_table = Table(summary_rows, colWidths=[130 * mm, 35 * mm], hAlign="RIGHT")
    summary_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("LINEABOVE", (0, -1), (-1, -1), 0.75, NAVY),
                ("TOPPADDING", (0, -1), (-1, -1), 6),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph("Thank you for learning with PyNotes.", normal))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def invoice_response(order):
    buffer = build_invoice_pdf(order)
    return FileResponse(
        buffer, as_attachment=True, filename=f"pynotes-invoice-{order.order_number}.pdf", content_type="application/pdf"
    )
