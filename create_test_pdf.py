#!/usr/bin/env python3
"""
Generate an "Official" 4-page test deposition PDF for the Black-Marker demo.
Uses pleading paper layout (line numbers 1-25, vertical margin borders, Courier font)
packed with fake PII, Financial, Medical, and Confidential data.
"""

import fitz  # PyMuPDF

# We format the transcript perfectly into 25-line pages.
PAGES = [
    # PAGE 1: Swearing In
    [
        "IN THE UNITED STATES DISTRICT COURT",
        "FOR THE NORTHERN DISTRICT OF CALIFORNIA",
        "",
        "JANE DOE,",
        "          Plaintiff,",
        "     vs.                               Case No. 2024-CV-08821",
        "NOVATECH SYSTEMS, INC.,",
        "          Defendant.",
        "__________________________________/",
        "",
        "VIDEOTAPED DEPOSITION OF MICHAEL DAVID HENDERSON",
        "",
        "October 12, 2024",
        "9:00 a.m.",
        "",
        "APPEARANCES:",
        "For the Plaintiff:  James Whitfield, Esq.",
        "For the Defendant:  Linda Torres, Esq.",
        "",
        "MICHAEL DAVID HENDERSON, having been first duly sworn,",
        "testified as follows:",
        "",
        "EXAMINATION BY MR. WHITFIELD:",
        "Q. Please state your full name for the record.",
        "A. My name is Michael David Henderson."
    ],
    # PAGE 2: PII, Employment & Proprietary Data
    [
        "Q. And your current home address?",
        "A. I reside at 4721 Maple Grove Drive, San Jose, CA 95129.",
        "Q. What is your date of birth?",
        "A. March 14, 1979.",
        "Q. And your Social Security Number for verification purposes?",
        "A. My SSN is 523-88-4471.",
        "Q. Thank you. Do you hold any other identifying licenses?",
        "A. I have a California Driver's License, number D8829104.",
        "Q. Let's discuss your employment history. You were employed",
        "   at NovaTech Systems, correct?",
        "A. Yes, I was a Senior Software Architect from 2019 to 2023.",
        "Q. During your employment, did you have access to Project",
        "   Nighthawk?",
        "A. I did. Project Nighthawk was our proprietary edge-inference",
        "   engine.",
        "Q. What was unique about this project?",
        "A. The core algorithm used a novel quantization technique we",
        "   called FluxReduce. It was highly classified.",
        "Q. Were you aware of Dr. Penelope Vance's involvement?",
        "A. Yes, she was the lead researcher on the team.",
        "Q. Do you have her contact information?",
        "A. Dr. Penelope Vance's personal cell was (555) 867-5309.",
        "Q. Did she work from the main office?",
        "A. Not always. She often worked from home at 990 Riverside",
        "   Apartments, Apt 4B."
    ],
    # PAGE 3: Medical & Financial Data
    [
        "Q. Mr. Henderson, regarding your counter-claim for emotional",
        "   distress and medical expenses, we need to ask a few",
        "   health-related questions.",
        "A. I understand.",
        "Q. Are you currently under treatment for any conditions?",
        "A. Yes, I have been managing Type 2 Diabetes.",
        "Q. Have you been prescribed any medication for this?",
        "A. I have been prescribed Metformin 500mg.",
        "Q. Who is your primary physician overseeing this treatment?",
        "A. I am seen by Dr. Carlos Reyes, at Mercy Medical Center.",
        "Q. Let's move to your current financial status. What is your",
        "   annual compensation at your new employer?",
        "A. My base salary is $185,000 plus equity.",
        "Q. And where are those funds deposited?",
        "A. My Checking Account ending in 4092 at First National",
        "   receives direct deposit. I also have a routing number of",
        "   122000661 for transfers.",
        "Q. Do you have any secondary income?",
        "A. No, just my primary salary.",
        "Q. What is your personal email for correspondence?",
        "A. It is m.henderson79@gmail.com.",
        "Q. Do you use encrypted email addresses for sensitive work?",
        "A. Yes, I also have a backup at shadow_coder@protonmail.com.",
        "Q. During the breach, logs show access from IP 192.168.100.45.",
        "A. Yes, that is the static IP of my home network router."
    ],
    # PAGE 4: Conclusion & Certificate
    [
        "Q. Are there any other digital aliases you use?",
        "A. My GitHub username is MikeH-Dev88, but that's public.",
        "Q. Thank you, Mr. Henderson. We have no further questions at",
        "   this time.",
        "A. Thank you.",
        "",
        "",
        "",
        "                      CERTIFICATE",
        "",
        "I, Rebecca Nguyen, Certified Court Reporter No. 8841, do",
        "hereby certify that the foregoing is a true and accurate",
        "transcript of the proceedings recorded by me in the matter",
        "of Jane Doe v. NovaTech Systems, Inc.",
        "",
        "Dated this 14th day of October, 2024.",
        "",
        "",
        "_________________________________",
        "Rebecca Nguyen, CCR #8841",
        "",
        "",
        "",
        "",
        ""
    ]
]

def generate_official_pdf(output_filename="test_deposition_OFFICIAL.pdf"):
    print(f"Generating Official Pleading Paper PDF: {output_filename}...")
    
    doc = fitz.open()
    
    # Standard Letter Size (8.5 x 11 inches = 612 x 792 points)
    PAGE_WIDTH = 612
    PAGE_HEIGHT = 792
    
    # Layout configuration
    LEFT_MARGIN = 72
    RIGHT_MARGIN = 540
    TOP_MARGIN = 72
    LINE_HEIGHT = 25  # Gives us ~25 lines per page beautifully
    
    for i, page_lines in enumerate(PAGES):
        page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        
        # 1. DRAW PLEADING PAPER BORDERS
        # Double line on the left
        page.draw_line(fitz.Point(LEFT_MARGIN, 36), fitz.Point(LEFT_MARGIN, PAGE_HEIGHT - 36), color=(0,0,0), width=1)
        page.draw_line(fitz.Point(LEFT_MARGIN + 4, 36), fitz.Point(LEFT_MARGIN + 4, PAGE_HEIGHT - 36), color=(0,0,0), width=1)
        # Single line on the right
        page.draw_line(fitz.Point(RIGHT_MARGIN, 36), fitz.Point(RIGHT_MARGIN, PAGE_HEIGHT - 36), color=(0,0,0), width=1)
        
        # 2. DRAW TEXT AND LINE NUMBERS
        current_y = TOP_MARGIN
        
        for line_num in range(1, 26):
            # Draw line number (1 to 25) aligned to the left of the double border
            page.insert_text(
                fitz.Point(LEFT_MARGIN - 20, current_y), 
                str(line_num), 
                fontsize=11, 
                fontname="helv", 
                color=(0.5, 0.5, 0.5) # Gray line numbers look professional
            )
            
            # Draw actual transcript text (if available for this line)
            if line_num - 1 < len(page_lines):
                text_content = page_lines[line_num - 1]
                if text_content.strip():
                    page.insert_text(
                        fitz.Point(LEFT_MARGIN + 15, current_y), 
                        text_content, 
                        fontsize=11.5, 
                        fontname="cour" # Courier - Monospaced Typewriter font
                    )
            
            # Move down to next line
            current_y += LINE_HEIGHT
            
        # Draw small page number at bottom center
        page.insert_text(
            fitz.Point(PAGE_WIDTH / 2 - 10, PAGE_HEIGHT - 30), 
            f"- {i+1} -", 
            fontsize=10, 
            fontname="helv"
        )
            
        print(f"  -> Formatted and inserted Page {i+1}")

    doc.save(output_filename)
    doc.close()
    
    print("\nDone! Your official demo file is ready.")
    print(f"Run it with: python run_async.py {output_filename}")

if __name__ == "__main__":
    generate_official_pdf()