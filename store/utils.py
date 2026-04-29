"""
PDF Receipt Generator using ReportLab
for Jay Bn Poultry Farm and Feeding Point
"""

import os
from io import BytesIO
from django.conf import settings as django_settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .models import SiteSettings, PaymentReceipt

# ── Font Registration (for Rupee Symbol support) ──────
def register_fonts():
    # Try common paths for DejaVuSans which supports Rupee (₹)
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",          # Linux (alt)
        "C:\\Windows\\Fonts\\arial.ttf",                   # Windows
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('DejaVuSans', path))
                return 'DejaVuSans'
            except:
                pass
    return 'Helvetica' # Fallback

UNICODE_FONT = register_fonts()


# ── Color palette (Mithila Gold Premium) ──────
GOLD = colors.HexColor('#C9962A')
GOLD_LIGHT = colors.HexColor('#E8B84B')
CRIMSON = colors.HexColor('#7A0C2E')
CRIMSON_DARK = colors.HexColor('#3D0617')
IVORY = colors.HexColor('#FDF6E3')
DARK = colors.HexColor('#120609')
TEXT_DARK = colors.HexColor('#120609')
TEXT_LIGHT = colors.HexColor('#FDF6E3')
BORDER_COLOR = colors.HexColor('#C9962A')
STRIPE_COLOR = colors.HexColor('#FFFDF9') # Very light ivory for rows


def _get_or_create_receipt(order=None, sales_record=None):
    if order:
        receipt, _ = PaymentReceipt.objects.get_or_create(order=order)
    else:
        receipt, _ = PaymentReceipt.objects.get_or_create(sales_record=sales_record)
    return receipt


def generate_order_receipt_pdf(order):
    """Generate a PDF receipt for an online Order."""
    receipt = _get_or_create_receipt(order=order)
    settings = SiteSettings.get_settings()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=1.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)

    items_data = [['Product', 'Qty', 'Rate (₹)', 'Total (₹)']]
    for item in order.items.all():
        items_data.append([
            item.product_name,
            str(item.quantity),
            f'₹{item.unit_price:,.2f}',
            f'₹{item.total:,.2f}'
        ])

    story = _build_receipt_story(
        doc=doc,
        settings=settings,
        receipt=receipt,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        customer_address=order.customer_address,
        date=order.created_at.date(),
        items_data=items_data,
        subtotal=order.subtotal,
        gst_amount=order.gst_amount,
        grand_total=order.total_amount,
        payment_mode=order.payment_mode,
    )

    doc.build(story, onFirstPage=_draw_watermark, onLaterPages=_draw_watermark)
    buffer.seek(0)
    return buffer


def generate_sales_receipt_pdf(sales_record):
    """Generate a PDF receipt for a manual SalesRecord."""
    receipt = _get_or_create_receipt(sales_record=sales_record)
    settings = SiteSettings.get_settings()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=1.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)

    items_data = [['Product', 'Qty', 'Rate (₹)', 'Total (₹)']]
    for item in sales_record.items.all():
        items_data.append([
            item.product_name,
            str(item.quantity),
            f'₹{item.unit_price:,.2f}',
            f'₹{item.total:,.2f}'
        ])

    story = _build_receipt_story(
        doc=doc,
        settings=settings,
        receipt=receipt,
        customer_name=sales_record.customer_name,
        customer_phone=sales_record.customer_phone,
        customer_address=sales_record.customer_address,
        date=sales_record.date,
        items_data=items_data,
        subtotal=sales_record.subtotal,
        gst_amount=sales_record.gst_amount,
        grand_total=sales_record.total_amount,
        payment_mode=sales_record.payment_mode,
    )

    doc.build(story, onFirstPage=_draw_watermark, onLaterPages=_draw_watermark)
    buffer.seek(0)
    return buffer


def _draw_watermark(canvas, doc):
    """Draw a subtle watermark in the background."""
    canvas.saveState()
    canvas.setFont('Times-Bold', 60)
    canvas.setStrokeColor(GOLD)
    canvas.setFillAlpha(0.04)
    canvas.translate(A4[0]/2, A4[1]/2)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "MITHILA GOLD")
    canvas.restoreState()


def _build_receipt_story(doc, settings, receipt, customer_name, customer_phone,
                          customer_address, date, items_data,
                          subtotal, gst_amount, grand_total, payment_mode):
    """Build the premium platypus story for the receipt PDF."""
    styles = getSampleStyleSheet()

    # Custom premium styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                  fontSize=26, textColor=CRIMSON,
                                  spaceAfter=4, alignment=TA_LEFT, fontName='Times-Bold')
    
    header_info_style = ParagraphStyle('HeaderInfo', parent=styles['Normal'],
                                        fontSize=10, alignment=TA_RIGHT, spaceAfter=2, textColor=DARK, leading=12)
    
    label_style = ParagraphStyle('Label', parent=styles['Normal'],
                                  fontSize=10, textColor=colors.grey, leading=12)
    
    invoice_title_style = ParagraphStyle('InvTitle', parent=styles['Normal'],
                                          fontSize=20, fontName='Times-Bold', textColor=CRIMSON)
    
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
                                   fontSize=10, textColor=colors.grey,
                                   alignment=TA_CENTER)

    story = []

    # ── Decorative Top Border ───────────────────
    story.append(HRFlowable(width="100%", thickness=3, color=GOLD, spaceAfter=10))

    # ── Header Layout ───────────────────────────
    logo_path = os.path.join(django_settings.BASE_DIR, 'static', 'img', 'logo.png')
    logo = None
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2.4*cm, height=2.4*cm)

    title_text = settings.company_name.upper()
    custom_title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                         fontSize=22, textColor=CRIMSON,
                                         alignment=TA_LEFT, fontName='Times-Bold')

    header_content_info = [
        Paragraph(f'<b>GSTIN: {settings.gst_number}</b>', header_info_style),
        Paragraph(settings.address, header_info_style),
        Paragraph(f'Phone: {settings.phone_primary} / {settings.phone_secondary}', header_info_style),
        Paragraph(f'Email: {settings.email or "N/A"}', header_info_style),
    ]

    title_para = Paragraph(title_text, custom_title_style)

    if logo:
        header_data = [[logo, title_para, header_content_info]]
        header_table = Table(header_data, colWidths=[2.8*cm, doc.width * 0.42, doc.width * 0.3])
    else:
        header_data = [[title_para, header_content_info]]
        header_table = Table(header_data, colWidths=[doc.width * 0.65, doc.width * 0.35])

    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=GOLD, spaceAfter=15, spaceBefore=4))

    # ── Invoice Title & Info ────────────────────
    invoice_data = [
        [
            Paragraph(f'<b>TAX INVOICE</b>', invoice_title_style),
            Paragraph(f'Invoice No: <b color="{CRIMSON}">#{receipt.receipt_number}</b>', ParagraphStyle('num', alignment=TA_RIGHT, fontSize=12, fontName='Times-Bold')),
        ],
        [
            Paragraph(f'BILL TO:', ParagraphStyle('bill', fontSize=11, textColor=GOLD, fontName='Times-Bold', spaceBefore=10)),
            Paragraph(f'Date: <b>{date.strftime("%d %b, %Y")}</b>', ParagraphStyle('dt', alignment=TA_RIGHT, fontSize=11)),
        ],
        [
            [
                Paragraph(f'<b>{customer_name}</b>', ParagraphStyle('cname', fontSize=13, leading=16, fontName='Times-Bold')),
                Paragraph(f'{customer_phone}', ParagraphStyle('cphone', fontSize=10, textColor=colors.grey, leading=12)),
                Paragraph(f'{customer_address or ""}', ParagraphStyle('caddr', fontSize=10, textColor=colors.grey, leading=12)),
            ],
            ''
        ]
    ]
    invoice_table = Table(invoice_data, colWidths=[doc.width * 0.7, doc.width * 0.3])
    invoice_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(invoice_table)
    story.append(Spacer(1, 15))

    # ── Items Table ──────────────────────────────
    if len(items_data) > 1:
        # Update header row
        items_data[0] = [Paragraph(f'<b>{c}</b>', ParagraphStyle('th', textColor=colors.white, fontSize=11, alignment=TA_LEFT if i==0 else TA_RIGHT)) for i, c in enumerate(items_data[0])]
        
        col_widths = [doc.width * 0.52, doc.width * 0.08, doc.width * 0.2, doc.width * 0.2]
        items_table = Table(items_data, colWidths=col_widths, repeatRows=1)
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), CRIMSON),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, STRIPE_COLOR]),
            ('LINEBELOW', (0, 0), (-1, 0), 2, GOLD),
            ('LINEBELOW', (0, -1), (-1, -1), 1, GOLD),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('FONTNAME', (2, 1), (3, -1), UNICODE_FONT if UNICODE_FONT != "Helvetica" else "Helvetica"),
        ]))
        story.append(items_table)
    else:
        story.append(Paragraph('No items recorded.', label_style))

    story.append(Spacer(1, 10))

    # ── Totals Layout ───────────────────────────
    summary_data = [
        ['', 'Subtotal', f'₹{subtotal:,.2f}'],
        ['', 'GST (5%)', f'₹{gst_amount:,.2f}'],
        ['', Paragraph(f'<b>TOTAL AMOUNT</b>', ParagraphStyle('gt', textColor=CRIMSON, fontSize=14, fontName='Times-Bold')), 
         Paragraph(f'<b>₹{grand_total:,.2f}</b>', ParagraphStyle('gtv', textColor=CRIMSON, fontSize=14, fontName=UNICODE_FONT if UNICODE_FONT != "Helvetica" else "Times-Bold", alignment=TA_RIGHT))],
        ['', 'Payment Method', f'<b>{payment_mode}</b>'],
    ]
    summary_table = Table(summary_data, colWidths=[doc.width * 0.5, doc.width * 0.25, doc.width * 0.25])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('TEXTCOLOR', (1, 0), (1, -1), DARK),
        ('FONTSIZE', (1, 0), (2, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEABOVE', (1, 2), (2, 2), 1, GOLD),
        ('LINEBELOW', (1, 2), (2, 2), 2, GOLD),
    ]))
    story.append(summary_table)

    # ── Terms & Footer ──────────────────────────
    story.append(Spacer(1, 40))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD))
    story.append(Spacer(1, 10))
    
    terms_text = """
    <b>Terms & Conditions:</b><br/>
    1. Goods once sold will not be taken back.<br/>
    2. This is a computer generated invoice and does not require a physical signature.<br/>
    3. Thank you for choosing Mithila Gold. We value your trust.
    """
    story.append(Paragraph(terms_text, ParagraphStyle('Terms', fontSize=8, textColor=colors.grey, leading=10)))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph('🪷 <b>MITHILA GOLD</b>', ParagraphStyle('f1', alignment=TA_CENTER, fontSize=12, textColor=CRIMSON, fontName='Times-Bold')))
    # Hindi tagline - using the registered Unicode font
    story.append(Paragraph('मिथिला की धरोहर — हर कौर में।', ParagraphStyle('f2', alignment=TA_CENTER, fontSize=10, textColor=GOLD, fontName=UNICODE_FONT)))

    return story
