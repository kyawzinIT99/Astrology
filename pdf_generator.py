"""
PDF Report Generator for Myanmar Astrology.

Generates professional PDF reports with Myanmar Unicode text
using fpdf2 and the Padauk font.
"""

import os
from datetime import datetime
from fpdf import FPDF
from mahabote_engine import MahaboteEngine, MahaboteReading


# Path to fonts directory
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "static", "reports")


class AstrologyPDF(FPDF):
    """Custom PDF class for astrology reports."""

    def __init__(self, reading: MahaboteReading):
        super().__init__()
        self.reading = reading
        self._setup_fonts()

    def _setup_fonts(self):
        """Register Myanmar Unicode font."""
        font_path = os.path.join(FONT_DIR, "Padauk-Regular.ttf")
        font_bold_path = os.path.join(FONT_DIR, "Padauk-Bold.ttf")

        if os.path.exists(font_path):
            self.add_font("Padauk", "", font_path)
        if os.path.exists(font_bold_path):
            self.add_font("Padauk", "B", font_bold_path)

        self._has_myanmar_font = os.path.exists(font_path)

    def _set_font_safe(self, style="", size=12):
        """Set font with fallback."""
        if self._has_myanmar_font:
            self.set_font("Padauk", style, size)
        else:
            self.set_font("Helvetica", style, size)

    def header(self):
        """Page header with gradient bar."""
        # Purple gradient header bar
        self.set_fill_color(88, 28, 135)
        self.rect(0, 0, 210, 35, "F")
        self.set_fill_color(139, 92, 246)
        self.rect(0, 30, 210, 5, "F")

        # Title
        self.set_text_color(255, 255, 255)
        self._set_font_safe("B", 18)
        self.set_y(8)
        if self._has_myanmar_font:
            self.cell(0, 12, "Su Mon Myint Oo မဟာဘုတ် ဗေဒင်(Tarot)", align="C", new_x="LMARGIN", new_y="NEXT")
        else:
            self.cell(0, 12, "Su Mon Myint Oo Mahabote Astrology (Tarot)", align="C", new_x="LMARGIN", new_y="NEXT")

        self.set_text_color(0, 0, 0)
        self.ln(15)

    def footer(self):
        """Page footer."""
        self.set_y(-20)
        self.set_text_color(128, 128, 128)
        self._set_font_safe("", 8)
        if self._has_myanmar_font:
            self.cell(0, 10, f"စာမျက်နှာ {self.page_no()}", align="C")
        else:
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def add_section_header(self, text_mm: str, text_en: str):
        """Add a styled section header."""
        self.set_fill_color(139, 92, 246)
        self.set_text_color(255, 255, 255)
        self._set_font_safe("B", 13)
        label = text_mm if self._has_myanmar_font else text_en
        self.cell(0, 10, f"  {label}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def add_info_row(self, label_mm: str, label_en: str, value_mm: str, value_en: str):
        """Add an info row with label and value."""
        self._set_font_safe("B", 11)
        label = label_mm if self._has_myanmar_font else label_en
        self.cell(60, 8, label)
        self._set_font_safe("", 11)
        value = value_mm if self._has_myanmar_font else value_en
        self.cell(0, 8, value, new_x="LMARGIN", new_y="NEXT")

    def add_paragraph(self, text_mm: str, text_en: str):
        """Add a paragraph."""
        self._set_font_safe("", 10)
        text = text_mm if self._has_myanmar_font else text_en
        self.multi_cell(0, 7, text)
        self.ln(2)

    def add_bullet(self, text_mm: str, text_en: str, icon: str = "- "):
        """Add a bullet point."""
        self._set_font_safe("", 10)
        self.set_x(self.l_margin)  # Reset x to left margin
        text = text_mm if self._has_myanmar_font else text_en
        self.multi_cell(0, 7, f"  {icon}{text}")


def generate_pdf(reading: MahaboteReading, engine: MahaboteEngine) -> str:
    """
    Generate a professional PDF report.
    Returns the file path of the generated PDF.
    """
    os.makedirs(REPORT_DIR, exist_ok=True)

    pdf = AstrologyPDF(reading)
    pdf.add_page()

    house = reading.house
    bd = reading.birth_day
    md = reading.myanmar_date

    # ── Personal Info Section ──
    pdf.add_section_header("ကိုယ်ရေးအချက်အလက်", "Personal Information")
    pdf.add_info_row("အမည်:", "Name:", reading.name, reading.name)
    pdf.add_info_row(
        "မွေးနေ့:", "Birth Date:",
        reading.birth_date.strftime("%Y-%m-%d"), reading.birth_date.strftime("%Y-%m-%d")
    )
    pdf.add_info_row(
        "မြန်မာရက်စွဲ:", "Myanmar Date:",
        md.display, f"ME {md.myanmar_year}, {md.month_name}"
    )
    pdf.add_info_row(
        "မြန်မာသက္ကရာဇ်:", "Myanmar Era:",
        f"{reading.myanmar_year} ခုနှစ်", str(reading.myanmar_year)
    )
    pdf.add_info_row(
        "မွေးနေ့:", "Birth Day:",
        f"{bd['name_mm']} ({bd['planet_mm']})",
        f"{bd['name_en']} ({bd['planet_en']})"
    )
    pdf.add_info_row(
        "ရာသီတိရစ္ဆာန်:", "Zodiac Animal:",
        bd['animal_mm'], bd['animal_en']
    )
    pdf.add_info_row(
        "ကံကောင်းသောဦးတည်ရာ:", "Lucky Direction:",
        bd['direction_mm'], bd['direction_mm']
    )
    pdf.ln(5)

    # ── House Analysis Section ──
    pdf.add_section_header("မဟာဘုတ်အိမ် ဆန်းစစ်ခြင်း", "Mahabote House Analysis")
    pdf.add_info_row(
        "မဟာဘုတ်အိမ်:", "House:",
        f"{house['name_mm']} ({house['name_en']})",
        f"{house['name_en']} ({house['planet_en']})"
    )
    pdf.add_info_row(
        "အိမ်ရှင်ဂြိုဟ်:", "Ruling Planet:",
        f"{house['planet_mm']} ({house['planet_en']})",
        f"{house['planet_en']}"
    )
    nature_mm = "ကောင်းသောအိမ်" if house['nature'] == 'asset' else "စိန်ခေါ်သောအိမ်"
    pdf.add_info_row(
        "သဘာဝ:", "Nature:",
        nature_mm, house['nature'].title()
    )
    pdf.add_info_row("ကြွင်းကိန်း:", "Remainder:", str(reading.house_remainder), str(reading.house_remainder))
    pdf.ln(3)

    # Personality
    pdf.add_section_header("ကိုယ်ရည်ကိုယ်သွေး", "Personality Profile")
    pdf.add_paragraph(house['personality_mm'], house['personality_en'])
    pdf.ln(2)

    # Strengths
    pdf._set_font_safe("B", 11)
    if pdf._has_myanmar_font:
        pdf.cell(0, 8, "အားသာချက်များ:", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 8, "Strengths:", new_x="LMARGIN", new_y="NEXT")
    for s in house.get("strengths_mm", []):
        pdf.add_bullet(s, s, "+ ")

    pdf.ln(2)

    # Weaknesses
    pdf._set_font_safe("B", 11)
    if pdf._has_myanmar_font:
        pdf.cell(0, 8, "သတိထားရန်:", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 8, "Caution:", new_x="LMARGIN", new_y="NEXT")
    for w in house.get("weaknesses_mm", []):
        pdf.add_bullet(w, w, "- ")

    # ── 6-Month Forecast Section ──
    pdf.add_page()
    pdf.add_section_header("၆ လ ဟောစာတမ်း", "6-Month Forecast")

    forecasts = engine.generate_6month_forecast(reading)
    for f in forecasts:
        # Month header
        pdf.set_fill_color(243, 232, 255)
        pdf._set_font_safe("B", 11)
        pdf.cell(0, 8, f"  {f['month_en']}", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

        # Modifier
        pdf._set_font_safe("", 10)
        pdf.set_text_color(88, 28, 135)
        if pdf._has_myanmar_font:
            pdf.cell(0, 7, f"    {f['modifier_mm']}", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.cell(0, 7, f"    {f['modifier_mm']}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

        # Do
        pdf.set_text_color(22, 101, 52)
        pdf.add_bullet(f"လုပ်သင့်သည်: {f['do_mm']}", f"DO: {f['do_mm']}", "[+] ")

        # Don't
        pdf.set_text_color(185, 28, 28)
        pdf.add_bullet(f"ရှောင်ကြဉ်ရန်: {f['dont_mm']}", f"DON'T: {f['dont_mm']}", "[-] ")

        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

    # Footer note
    pdf.ln(10)
    pdf.set_text_color(128, 128, 128)
    pdf._set_font_safe("", 8)
    gen_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    if pdf._has_myanmar_font:
        pdf.cell(0, 7, f"ဤဟောစာတမ်းကို {gen_date} တွင် ထုတ်လုပ်ထားပါသည်။", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, "မြန်မာ မဟာဘုတ် ဗေဒင် အခြေခံ တွက်ချက်မှုများ ပါဝင်ပါသည်။", align="C")
    else:
        pdf.cell(0, 7, f"Generated on {gen_date}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, "Based on traditional Myanmar Mahabote astrology calculations.", align="C")

    # Save
    safe_name = "".join(c for c in reading.name if c.isalnum() or c in " _-").strip()
    if not safe_name:
        safe_name = "report"
    filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(REPORT_DIR, filename)
    pdf.output(filepath)

    return filepath


if __name__ == "__main__":
    engine = MahaboteEngine()
    reading = engine.calculate("တက်ဇော်", 1990, 5, 15)
    path = generate_pdf(reading, engine)
    print(f"PDF generated: {path}")
