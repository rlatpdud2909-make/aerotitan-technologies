from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BannerDemo',parent=styles['Normal'],fontSize=8,leading=11,textColor=colors.HexColor('#9a2830'),alignment=TA_CENTER,spaceAfter=9))
styles.add(ParagraphStyle(name='SmallDemo',parent=styles['Normal'],fontSize=8,leading=11))
styles.add(ParagraphStyle(name='HeadingDemo',parent=styles['Heading2'],textColor=colors.HexColor('#284b63'),spaceBefore=8,spaceAfter=5))

def table(rows, widths=None):
    t=Table([[Paragraph(str(v),styles['SmallDemo']) for v in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eff2')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#b8c2cc')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    return t

def make_pdf(path,title,subtitle,blocks):
    doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=38,leftMargin=38,topMargin=32,bottomMargin=32,title=title)
    story=[Paragraph('SYNTHETIC TEST DATA — EDUCATIONAL USE ONLY<br/>NOT VALID FOR MATERIAL ACCEPTANCE',styles['BannerDemo']),Paragraph(title,styles['Title']),Paragraph(subtitle,styles['Normal']),Spacer(1,10)]
    for heading, rows in blocks:
        story.extend([Paragraph(heading,styles['HeadingDemo']),table(rows),Spacer(1,5)])
    story.append(Paragraph('DEMO_SPEC_TI64_V1 is an invented educational purchase requirement, not SAE or a material acceptance specification.',styles['SmallDemo']))
    doc.build(story)

