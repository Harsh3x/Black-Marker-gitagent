#!/usr/bin/env python3
"""Generate a realistic mock legal deposition PDF for testing Black-Marker."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER

def create_test_deposition():
    doc = SimpleDocTemplate(
        "test_deposition.pdf",
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    bold = ParagraphStyle("bold", parent=normal, fontName="Helvetica-Bold")
    center = ParagraphStyle("center", parent=normal, alignment=TA_CENTER)
    heading = ParagraphStyle("heading", parent=normal, fontName="Helvetica-Bold", fontSize=12)

    story = []

    story.append(Paragraph("IN THE UNITED STATES DISTRICT COURT", center))
    story.append(Paragraph("NORTHERN DISTRICT OF CALIFORNIA", center))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Case No. 2024-CV-08821", center))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("DEPOSITION OF MICHAEL R. HENDERSON", heading))
    story.append(Paragraph("Taken on behalf of the Plaintiff", normal))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "APPEARANCES: Present were Attorney James Whitfield for the plaintiff, "
        "Attorney Linda Torres for the defense, and the court reporter.",
        normal
    ))
    story.append(Spacer(1, 0.2*inch))

    deposition_text = [
        ("Q:", "Please state your full name for the record."),
        ("A:", "My name is Michael Robert Henderson."),
        ("Q:", "And your current home address?"),
        ("A:", "I reside at 4721 Maple Grove Drive, Apt 3B, San Jose, California 95128."),
        ("Q:", "What is your date of birth?"),
        ("A:", "March 14, 1979."),
        ("Q:", "And your Social Security Number for verification purposes?"),
        ("A:", "My SSN is 523-88-4471."),
        ("Q:", "Mr. Henderson, you were employed at NovaTech Systems, correct?"),
        ("A:", "Yes, I was a Senior Software Architect from 2019 through 2023."),
        ("Q:", "During your employment, did you have access to Project Nighthawk?"),
        ("A:", "I did. Project Nighthawk was our proprietary edge-inference engine. "
               "The core algorithm used a novel quantization technique we called FluxReduce."),
        ("Q:", "Were you aware of your colleague Dr. Sarah J. Patel's involvement?"),
        ("A:", "Yes. Dr. Patel was the lead architect. Her personal cell was 408-552-9931 "
               "and she often worked from home at 892 Orchard Lane, Cupertino."),
        ("Q:", "Mr. Henderson, are you currently under treatment for any conditions?"),
        ("A:", "I have been managing Type 2 diabetes and have been prescribed Metformin 1000mg "
               "by my physician, Dr. Carlos Reyes at Valley Medical Center."),
        ("Q:", "What is your current annual compensation at your new employer?"),
        ("A:", "My base salary is $247,500 plus equity. My bank account ending 4829 "
               "at First National receives direct deposit."),
        ("Q:", "One last question — your personal email for correspondence?"),
        ("A:", "It is m.henderson79@gmail.com. I also have a backup at mike_h1979@yahoo.com."),
    ]

    for speaker, text in deposition_text:
        story.append(Paragraph(f"<b>{speaker}</b> {text}", normal))
        story.append(Spacer(1, 0.1*inch))

    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "CERTIFICATE: I, Rebecca Nguyen, Certified Court Reporter No. 8841, "
        "do hereby certify that the foregoing is a true and accurate transcript.",
        normal
    ))

    doc.build(story)
    print("✓ Created test_deposition.pdf")

if __name__ == "__main__":
    create_test_deposition()