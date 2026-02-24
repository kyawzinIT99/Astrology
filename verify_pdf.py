
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from mahabote_engine import MahaboteEngine
from pdf_generator import generate_pdf

def generate_test_pdf():
    print("Generating Test PDF for Dr.Tarot...")
    engine = MahaboteEngine()
    
    # Oct 10, 1978
    reading = engine.calculate("Dr.Tarot", 1978, 10, 10)
    
    pdf_path = generate_pdf(reading, engine)
    print(f"✅ PDF Generated at: {pdf_path}")
    
    # Print out core bits for manual terminal check
    print(f"Birth House: {reading.house['name_en']}")
    print(f"Age: {reading.current_age}")
    print(f"Current Year House: {reading.current_year_house['name_en']}")

if __name__ == "__main__":
    generate_test_pdf()
