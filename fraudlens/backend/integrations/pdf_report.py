"""
PDF Forensic Report Generator

Generates detailed forensic analysis reports in PDF format with 6 sections:
1. Header & ID
2. Forensic Identity
3. Visual Evidence
4. Technical Analysis
5. Metadata Snapshot
6. Disclaimer & Authentication
"""

from fpdf import FPDF
from datetime import datetime
from typing import Dict, Optional
import hashlib
import io
import logging
from PIL import Image

logger = logging.getLogger(__name__)


class ForensicReportPDF(FPDF):
    """Custom PDF class with header/footer"""

    def __init__(self, report_id: str):
        super().__init__()
        self.report_id = report_id
        self.generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    def header(self):
        """Page header with logo placeholder and report ID"""
        self.set_font('Arial', 'B', 12)
        self.set_text_color(51, 51, 51)
        self.cell(0, 10, 'TruthSnap Forensic Analysis Report', 0, 1, 'C')
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, f'Report ID: {self.report_id}', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        """Page footer with page numbers and generation time"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | Generated: {self.generated_at}', 0, 0, 'C')


class PDFReportGenerator:
    """
    Generates comprehensive forensic analysis PDF reports
    """

    def __init__(self):
        self.colors = {
            'primary': (41, 98, 255),      # Blue
            'success': (16, 185, 129),     # Green
            'warning': (245, 158, 11),     # Orange
            'danger': (239, 68, 68),       # Red
            'gray': (156, 163, 175),       # Gray
            'dark': (31, 41, 55),          # Dark gray
        }

    async def generate_report(
        self,
        image_bytes: bytes,
        analysis_result: Dict,
        include_image: bool = True
    ) -> bytes:
        """
        Generate comprehensive forensic PDF report

        Args:
            image_bytes: Original image data
            analysis_result: Full analysis results from API
            include_image: Whether to embed analyzed image

        Returns:
            PDF file as bytes
        """
        try:
            # Generate report ID
            report_id = self._generate_report_id(image_bytes)

            # Initialize PDF
            pdf = ForensicReportPDF(report_id)
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # Section 1: Header & ID
            self._add_header_section(pdf, report_id, analysis_result)

            # Section 2: Forensic Identity
            self._add_forensic_identity(pdf, image_bytes, analysis_result)

            # Section 3: Visual Evidence
            if include_image:
                self._add_visual_evidence(pdf, image_bytes, analysis_result)

            # Section 4: Technical Analysis
            self._add_technical_analysis(pdf, analysis_result)

            # Section 5: Metadata Snapshot
            self._add_metadata_section(pdf, analysis_result)

            # Section 6: Disclaimer & Authentication
            self._add_disclaimer_section(pdf, report_id)

            # Generate PDF output
            # pdf.output(dest='S') returns bytearray in fpdf2
            pdf_bytes = bytes(pdf.output(dest='S'))

            logger.info(f"Generated PDF report: {report_id} ({len(pdf_bytes)} bytes)")
            return pdf_bytes

        except Exception as e:
            logger.error(f"PDF generation failed: {e}", exc_info=True)
            raise

    def _generate_report_id(self, image_bytes: bytes) -> str:
        """Generate unique report ID based on image hash and timestamp"""
        image_hash = hashlib.sha256(image_bytes).hexdigest()[:12]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"TS-{timestamp}-{image_hash.upper()}"

    def _add_header_section(self, pdf: ForensicReportPDF, report_id: str, result: Dict):
        """Section 1: Header & ID"""
        # Title
        pdf.set_font('Arial', 'B', 18)
        pdf.set_text_color(*self.colors['dark'])
        pdf.cell(0, 10, 'FORENSIC ANALYSIS REPORT', 0, 1, 'C')
        pdf.ln(5)

        # Verdict badge
        verdict = result.get('verdict', 'inconclusive')
        confidence = result.get('confidence', 0.0)

        color = self._get_verdict_color(verdict)
        pdf.set_fill_color(*color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 14)

        verdict_text = verdict.replace('_', ' ').upper()
        badge_width = pdf.get_string_width(verdict_text) + 20
        x_pos = (pdf.w - badge_width) / 2
        pdf.set_x(x_pos)
        pdf.cell(badge_width, 12, verdict_text, 0, 1, 'C', fill=True)

        # Confidence score
        pdf.ln(5)
        pdf.set_text_color(*self.colors['dark'])
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 8, f'Confidence: {confidence*100:.1f}%', 0, 1, 'C')
        pdf.ln(8)

        # Separator
        pdf.set_draw_color(*self.colors['gray'])
        pdf.line(20, pdf.get_y(), pdf.w - 20, pdf.get_y())
        pdf.ln(10)

    def _add_forensic_identity(self, pdf: ForensicReportPDF, image_bytes: bytes, result: Dict):
        """Section 2: Forensic Identity"""
        self._add_section_title(pdf, '1. FORENSIC IDENTITY')

        # Image hash (SHA-256 is always exactly 64 characters)
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        self._add_field(pdf, 'SHA-256 Hash:', image_hash)

        # File metadata
        try:
            img = Image.open(io.BytesIO(image_bytes))
            self._add_field(pdf, 'Image Format:', img.format or 'Unknown')
            self._add_field(pdf, 'Dimensions:', f'{img.size[0]} × {img.size[1]} pixels')
            self._add_field(pdf, 'Color Mode:', img.mode)
        except:
            pass

        self._add_field(pdf, 'File Size:', f'{len(image_bytes):,} bytes')
        self._add_field(pdf, 'Analysis Date:', datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"))

        # Processing time
        proc_time = result.get('processing_time_ms', 0)
        self._add_field(pdf, 'Processing Time:', f'{proc_time:,} ms ({proc_time/1000:.2f}s)')

        pdf.ln(2)  # Reduced spacing before next section

    def _add_visual_evidence(self, pdf: ForensicReportPDF, image_bytes: bytes, result: Dict):
        """Section 3: Visual Evidence"""
        self._add_section_title(pdf, '2. VISUAL EVIDENCE')

        try:
            # Save image to temp file and embed
            img = Image.open(io.BytesIO(image_bytes))

            # Resize if needed
            max_width = 170  # Max width in PDF units
            max_height = 120

            ratio = min(max_width / img.size[0], max_height / img.size[1], 1.0)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))

            if ratio < 1.0:
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background

            # Save to temp buffer
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=85)
            img_buffer.seek(0)

            # Embed image
            x_pos = (pdf.w - new_size[0]) / 2
            pdf.image(img_buffer, x=x_pos, y=pdf.get_y(), w=new_size[0])
            pdf.ln(new_size[1] + 10)

            # Add caption
            pdf.set_font('Arial', 'I', 9)
            pdf.set_text_color(*self.colors['gray'])
            pdf.cell(0, 5, 'Analyzed image (embedded for reference)', 0, 1, 'C')
            pdf.set_text_color(*self.colors['dark'])

        except Exception as e:
            logger.warning(f"Failed to embed image in PDF: {e}")
            pdf.set_font('Arial', 'I', 10)
            pdf.set_text_color(*self.colors['gray'])
            pdf.cell(0, 8, '[Image embedding failed - see original file]', 0, 1, 'C')

        pdf.ln(5)

    def _add_technical_analysis(self, pdf: ForensicReportPDF, result: Dict):
        """Section 4: Technical Analysis"""
        self._add_section_title(pdf, '3. TECHNICAL ANALYSIS')

        # Watermark detection
        if result.get('watermark_detected'):
            watermark = result.get('watermark_analysis', {})
            self._add_subsection(pdf, 'Digital Watermark Detection')
            self._add_field(pdf, 'Status:', 'DETECTED', color=self.colors['danger'])
            self._add_field(pdf, 'Type:', watermark.get('type', 'Unknown'))
            self._add_field(pdf, 'Confidence:', f"{watermark.get('confidence', 0)*100:.1f}%")
            pdf.ln(3)
        else:
            self._add_subsection(pdf, 'Digital Watermark Detection')
            self._add_field(pdf, 'Status:', 'Not detected', color=self.colors['success'])
            pdf.ln(3)

        # Metadata validation
        if 'metadata_validation' in result:
            validation = result['metadata_validation']
            self._add_subsection(pdf, 'Metadata Validation (10-Layer Analysis)')

            score = validation.get('score', 0)
            risk_level = validation.get('risk_level', 'UNKNOWN')

            score_color = self._get_risk_color(risk_level)

            # Score field
            pdf.set_font('Arial', 'B', 9)
            pdf.set_text_color(*self.colors['dark'])
            pdf.cell(50, 5, 'Score:', 0, 0)
            pdf.set_font('Arial', '', 9)
            pdf.set_text_color(*score_color)
            pdf.cell(0, 5, f"{score}/100", 0, 1)

            # Risk Level field
            pdf.set_font('Arial', 'B', 9)
            pdf.set_text_color(*self.colors['dark'])
            pdf.cell(50, 5, 'Risk Level:', 0, 0)
            pdf.set_font('Arial', '', 9)
            pdf.set_text_color(*score_color)
            pdf.cell(0, 5, risk_level, 0, 1)

            # Red flags
            red_flags = validation.get('red_flags', [])
            if red_flags:
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(0, 6, 'Red Flags:', 0, 1)
                pdf.set_font('Arial', '', 9)
                for flag in red_flags[:5]:  # Limit to 5
                    reason = flag.get('reason', 'Unknown')
                    severity = flag.get('severity', 'unknown')
                    # Set X position for indentation
                    pdf.set_x(pdf.l_margin + 10)
                    # Calculate width: page width - margins - indent
                    text_width = pdf.w - pdf.l_margin - pdf.r_margin - 10
                    pdf.multi_cell(text_width, 5, f"- [{severity.upper()}] {reason}")

            pdf.ln(3)

        # FFT Analysis
        if 'fft_analysis' in result:
            fft = result['fft_analysis']
            self._add_subsection(pdf, 'FFT Frequency Analysis')

            fft_score = fft.get('score', 0.5)
            fft_color = self.colors['danger'] if fft_score > 0.7 else self.colors['success']

            # AI Generation Score field
            pdf.set_font('Arial', 'B', 9)
            pdf.set_text_color(*self.colors['dark'])
            pdf.cell(50, 5, 'AI Generation Score:', 0, 0)
            pdf.set_font('Arial', '', 9)
            pdf.set_text_color(*fft_color)
            pdf.cell(0, 5, f"{fft_score:.2f}", 0, 1)

            checks = fft.get('checks', [])
            if checks:
                pdf.set_font('Arial', '', 9)
                pdf.set_text_color(*self.colors['dark'])
                for check in checks[:3]:
                    result_text = check.get('result', '').strip()
                    # Skip empty results
                    if not result_text:
                        continue
                    # Set X position for indentation
                    pdf.set_x(pdf.l_margin + 10)
                    # Calculate width: page width - margins - indent
                    text_width = pdf.w - pdf.l_margin - pdf.r_margin - 10
                    pdf.multi_cell(text_width, 5, f"- {result_text}")

            pdf.ln(2)  # Reduced spacing

        # Face Swap Detection
        if 'face_swap_analysis' in result:
            face_swap = result['face_swap_analysis']
            faces = face_swap.get('faces_detected', 0)

            if faces > 0:
                self._add_subsection(pdf, 'Face Swap / Deepfake Detection')

                swap_score = face_swap.get('score', 0.0)
                swap_color = self.colors['danger'] if swap_score > 0.7 else self.colors['success']

                # Faces Detected field
                pdf.set_font('Arial', 'B', 9)
                pdf.set_text_color(*self.colors['dark'])
                pdf.cell(50, 5, 'Faces Detected:', 0, 0)
                pdf.set_font('Arial', '', 9)
                pdf.cell(0, 5, str(faces), 0, 1)

                # Deepfake Score field
                pdf.set_font('Arial', 'B', 9)
                pdf.set_text_color(*self.colors['dark'])
                pdf.cell(50, 5, 'Deepfake Score:', 0, 0)
                pdf.set_font('Arial', '', 9)
                pdf.set_text_color(*swap_color)
                pdf.cell(0, 5, f"{swap_score:.2f}", 0, 1)

                pdf.ln(3)

        pdf.ln(2)

    def _add_metadata_section(self, pdf: ForensicReportPDF, result: Dict):
        """Section 5: Metadata Snapshot"""
        self._add_section_title(pdf, '4. METADATA SNAPSHOT')

        metadata = result.get('metadata', {})
        exif = metadata.get('exif', {})

        if exif:
            # Important EXIF fields
            important_fields = [
                ('Make', 'Camera Make'),
                ('Model', 'Camera Model'),
                ('Software', 'Software'),
                ('DateTime', 'Date/Time'),
                ('DateTimeOriginal', 'Original Date'),
                ('GPSInfo', 'GPS Data'),
            ]

            for exif_key, display_name in important_fields:
                if exif_key in exif:
                    value = str(exif[exif_key])
                    if len(value) > 60:
                        value = value[:57] + '...'
                    self._add_field(pdf, display_name + ':', value)

            # Show total EXIF fields
            pdf.ln(2)
            pdf.set_font('Arial', 'I', 9)
            pdf.set_text_color(*self.colors['gray'])
            pdf.cell(0, 5, f'Total EXIF fields: {len(exif)}', 0, 1)
            pdf.set_text_color(*self.colors['dark'])

        else:
            pdf.set_font('Arial', 'I', 10)
            pdf.set_text_color(*self.colors['gray'])
            pdf.cell(0, 8, 'No EXIF metadata found', 0, 1)
            pdf.set_text_color(*self.colors['dark'])

        pdf.ln(5)

    def _add_disclaimer_section(self, pdf: ForensicReportPDF, report_id: str):
        """Section 6: Disclaimer & Authentication"""
        self._add_section_title(pdf, '5. DISCLAIMER & AUTHENTICATION')

        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(*self.colors['dark'])

        disclaimer_text = (
            "This forensic analysis report is generated by TruthSnap's automated detection system. "
            "The findings are based on digital forensics techniques including metadata analysis, "
            "frequency domain analysis (FFT), watermark detection, and AI-generation heuristics.\n\n"
            "IMPORTANT LIMITATIONS:\n"
            "- This analysis is probabilistic, not definitive proof\n"
            "- AI detection technology is rapidly evolving\n"
            "- False positives and false negatives are possible\n"
            "- Professional photo editing may trigger false positives\n"
            "- This report should be used as supporting evidence, not sole proof\n\n"
            "For critical cases, manual expert review is recommended.\n\n"
        )

        pdf.multi_cell(0, 5, disclaimer_text)

        # Authentication signature
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(0, 5, 'Report Authentication', 0, 1)
        pdf.set_font('Arial', '', 9)

        # Generate report signature (hash of report ID + timestamp)
        signature = hashlib.sha256(
            f"{report_id}{pdf.generated_at}".encode()
        ).hexdigest()[:32]

        self._add_field(pdf, 'Report ID:', report_id)
        self._add_field(pdf, 'Signature:', signature.upper())
        self._add_field(pdf, 'Generated:', pdf.generated_at)

        pdf.ln(5)
        pdf.set_font('Arial', 'I', 8)
        pdf.set_text_color(*self.colors['gray'])
        pdf.cell(0, 5, 'TruthSnap - Automated Image Forensics | https://truthsnap.ai', 0, 1, 'C')

    # Helper methods

    def _add_section_title(self, pdf: ForensicReportPDF, title: str):
        """Add section title with underline"""
        pdf.set_font('Arial', 'B', 13)
        pdf.set_text_color(*self.colors['primary'])
        pdf.cell(0, 8, title, 0, 1)
        pdf.set_draw_color(*self.colors['primary'])
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.w - 20, pdf.get_y())
        pdf.ln(4)  # Reduced from 6 to 4
        pdf.set_text_color(*self.colors['dark'])

    def _add_subsection(self, pdf: ForensicReportPDF, title: str):
        """Add subsection title"""
        pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(*self.colors['dark'])
        pdf.cell(0, 6, title, 0, 1)
        pdf.ln(2)

    def _add_field(self, pdf: ForensicReportPDF, label: str, value: str, color=None):
        """Add labeled field"""
        if color is None:
            color = self.colors['dark']

        # Label
        pdf.set_font('Arial', 'B', 9)
        pdf.set_text_color(*self.colors['dark'])
        pdf.cell(50, 5, label, 0, 0)

        # Value - calculate remaining width
        # Page width = 210mm (A4), margins = 20mm each, label = 50mm
        value_width = pdf.w - pdf.l_margin - pdf.r_margin - 50

        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(*color)
        pdf.multi_cell(value_width, 5, value)

        # Reset X position to left margin for next field
        pdf.set_x(pdf.l_margin)

    def _get_verdict_color(self, verdict: str) -> tuple:
        """Get color for verdict badge"""
        color_map = {
            'real': self.colors['success'],
            'ai_generated': self.colors['danger'],
            'manipulated': self.colors['warning'],
            'inconclusive': self.colors['gray'],
        }
        return color_map.get(verdict, self.colors['gray'])

    def _get_risk_color(self, risk_level: str) -> tuple:
        """Get color for risk level"""
        color_map = {
            'CRITICAL': self.colors['danger'],
            'HIGH': self.colors['warning'],
            'MEDIUM': self.colors['gray'],
            'LOW': self.colors['success'],
        }
        return color_map.get(risk_level, self.colors['gray'])
