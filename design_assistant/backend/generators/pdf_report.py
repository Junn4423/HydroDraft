"""
PDF Report Generator - Sprint 4: Professional Reporting

Tạo báo cáo kỹ thuật PDF chuyên nghiệp:
- Technical reports với đầy đủ nội dung kỹ thuật
- Calculation appendix với công thức chi tiết
- Drawing index
- Authority submission documents
- Hỗ trợ font tiếng Việt (Unicode)
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import os
import io
import base64
import sys

# PDF generation library
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape, A3
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm, inch
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, ListFlowable, ListItem, KeepTogether,
        NextPageTemplate, FrameBreak
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
    from reportlab.graphics.shapes import Drawing, Line, Rect
    from reportlab.graphics import renderPDF
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    # Define fallback values when reportlab is not available
    A4 = (595.27, 841.89)  # A4 size in points
    mm = 2.834645669291339  # 1mm in points
    cm = 28.346456692913385  # 1cm in points
    print("Warning: reportlab chưa được cài đặt. Chức năng xuất PDF sẽ bị giới hạn.")


class ReportType(str, Enum):
    """Loại báo cáo"""
    TECHNICAL = "technical"           # Báo cáo kỹ thuật tổng hợp
    CALCULATION = "calculation"       # Thuyết minh tính toán
    DRAWING_INDEX = "drawing_index"   # Bảng kê bản vẽ
    AUTHORITY = "authority"           # Báo cáo nộp cơ quan
    SUMMARY = "summary"              # Tóm tắt dự án


class ReportLanguage(str, Enum):
    """Ngôn ngữ báo cáo"""
    VIETNAMESE = "vi"
    ENGLISH = "en"


@dataclass
class ReportConfig:
    """Cấu hình báo cáo"""
    title: str = "Báo Cáo Kỹ Thuật"
    subtitle: str = ""
    project_name: str = ""
    project_code: str = ""
    client: str = ""
    location: str = ""
    
    # Author info
    prepared_by: str = "HydroDraft"
    checked_by: str = ""
    approved_by: str = ""
    
    # Company info
    company_name: str = "HydroDraft Engineering"
    company_address: str = ""
    company_phone: str = ""
    company_email: str = ""
    
    # Dates
    date: datetime = field(default_factory=datetime.now)
    revision: str = "R0"
    
    # Layout
    page_size: Tuple[float, float] = A4
    margin_top: float = 25 * mm
    margin_bottom: float = 25 * mm
    margin_left: float = 25 * mm
    margin_right: float = 20 * mm
    
    # Language
    language: ReportLanguage = ReportLanguage.VIETNAMESE
    
    # Logo
    logo_path: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "project_name": self.project_name,
            "project_code": self.project_code,
            "client": self.client,
            "location": self.location,
            "prepared_by": self.prepared_by,
            "checked_by": self.checked_by,
            "approved_by": self.approved_by,
            "date": self.date.strftime("%d/%m/%Y"),
            "revision": self.revision
        }


@dataclass
class ReportSection:
    """Một phần trong báo cáo"""
    title: str
    content: str = ""
    level: int = 1  # 1=Chương, 2=Mục, 3=Tiểu mục
    tables: List[Dict] = field(default_factory=list)
    figures: List[Dict] = field(default_factory=list)
    subsections: List['ReportSection'] = field(default_factory=list)


class PDFReportGenerator:
    """
    Tạo báo cáo PDF chuyên nghiệp với hỗ trợ đầy đủ tiếng Việt
    
    Features:
    - Multi-language support (VN/EN) với Unicode fonts
    - TCVN-compliant formatting
    - Calculation appendix với công thức chi tiết
    - Drawing index
    - Version tracking
    - Professional layout và styles
    """
    
    # Vietnamese text labels
    LABELS_VI = {
        "table_of_contents": "MỤC LỤC",
        "chapter": "Chương",
        "section": "Mục",
        "figure": "Hình",
        "table": "Bảng",
        "page": "Trang",
        "prepared_by": "Người lập",
        "checked_by": "Người kiểm tra",
        "approved_by": "Người phê duyệt",
        "date": "Ngày",
        "revision": "Phiên bản",
        "project": "Dự án",
        "client": "Chủ đầu tư",
        "location": "Địa điểm",
        "drawing_no": "Số bản vẽ",
        "drawing_name": "Tên bản vẽ",
        "scale": "Tỷ lệ",
        "size": "Khổ giấy",
        "calculation_results": "Kết quả tính toán",
        "input_parameters": "Thông số đầu vào",
        "references": "Tài liệu tham chiếu",
        "conclusions": "Kết luận và kiến nghị",
        "appendix": "Phụ lục",
        "unit": "Đơn vị",
        "value": "Giá trị",
        "parameter": "Thông số",
        "description": "Mô tả",
        "formula": "Công thức",
        "result": "Kết quả",
        "standard": "Tiêu chuẩn",
        "note": "Ghi chú"
    }
    
    LABELS_EN = {
        "table_of_contents": "TABLE OF CONTENTS",
        "chapter": "Chapter",
        "section": "Section",
        "figure": "Figure",
        "table": "Table",
        "page": "Page",
        "prepared_by": "Prepared by",
        "checked_by": "Checked by",
        "approved_by": "Approved by",
        "date": "Date",
        "revision": "Revision",
        "project": "Project",
        "client": "Client",
        "location": "Location",
        "drawing_no": "Drawing No.",
        "drawing_name": "Drawing Name",
        "scale": "Scale",
        "size": "Size",
        "calculation_results": "Calculation Results",
        "input_parameters": "Input Parameters",
        "references": "References",
        "conclusions": "Conclusions & Recommendations",
        "appendix": "Appendix",
        "unit": "Unit",
        "value": "Value",
        "parameter": "Parameter",
        "description": "Description",
        "formula": "Formula",
        "result": "Result",
        "standard": "Standard",
        "note": "Note"
    }
    
    # Tiêu chuẩn thiết kế Việt Nam
    TCVN_STANDARDS = {
        "TCVN 7957:2008": "Thoát nước - Mạng lưới và công trình bên ngoài - Tiêu chuẩn thiết kế",
        "TCVN 51:2008": "Thoát nước - Mạng lưới bên trong và ngoài công trình",
        "QCVN 14:2008/BTNMT": "Quy chuẩn kỹ thuật quốc gia về nước thải sinh hoạt",
        "TCVN 4447:2012": "Công tác bê tông và bê tông cốt thép thi công và nghiệm thu",
        "TCVN 5574:2018": "Thiết kế kết cấu bê tông và bê tông cốt thép",
        "TCVN 2737:1995": "Tải trọng và tác động - Tiêu chuẩn thiết kế",
        "TCVN 9362:2012": "Tiêu chuẩn thiết kế nền nhà và công trình"
    }
    
    def __init__(self, output_dir: str = "./outputs/reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.config = ReportConfig()
        self.sections: List[ReportSection] = []
        self.styles = None
        self.labels = self.LABELS_VI
        self._styles_initialized = False
        self._fonts_registered = False
        
        if REPORTLAB_AVAILABLE:
            self._register_fonts()
            self._setup_styles()
    
    def _register_fonts(self):
        """Đăng ký font Unicode hỗ trợ tiếng Việt"""
        if self._fonts_registered:
            return
        
        # Tìm font paths - ưu tiên font có sẵn trên Windows
        font_paths = []
        
        # Windows font paths
        if sys.platform == 'win32':
            windows_fonts = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
            font_paths.extend([
                os.path.join(windows_fonts, 'arial.ttf'),
                os.path.join(windows_fonts, 'arialbd.ttf'),
                os.path.join(windows_fonts, 'ariali.ttf'),
                os.path.join(windows_fonts, 'times.ttf'),
                os.path.join(windows_fonts, 'timesbd.ttf'),
                os.path.join(windows_fonts, 'timesi.ttf'),
                os.path.join(windows_fonts, 'tahoma.ttf'),
                os.path.join(windows_fonts, 'tahomabd.ttf'),
            ])
        
        # Đăng ký Arial (hỗ trợ tiếng Việt tốt)
        try:
            if sys.platform == 'win32':
                windows_fonts = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
                
                arial_regular = os.path.join(windows_fonts, 'arial.ttf')
                arial_bold = os.path.join(windows_fonts, 'arialbd.ttf')
                arial_italic = os.path.join(windows_fonts, 'ariali.ttf')
                arial_bold_italic = os.path.join(windows_fonts, 'arialbi.ttf')
                
                if os.path.exists(arial_regular):
                    pdfmetrics.registerFont(TTFont('Arial', arial_regular))
                if os.path.exists(arial_bold):
                    pdfmetrics.registerFont(TTFont('Arial-Bold', arial_bold))
                if os.path.exists(arial_italic):
                    pdfmetrics.registerFont(TTFont('Arial-Italic', arial_italic))
                if os.path.exists(arial_bold_italic):
                    pdfmetrics.registerFont(TTFont('Arial-BoldItalic', arial_bold_italic))
                
                # Đăng ký Times New Roman
                times_regular = os.path.join(windows_fonts, 'times.ttf')
                times_bold = os.path.join(windows_fonts, 'timesbd.ttf')
                times_italic = os.path.join(windows_fonts, 'timesi.ttf')
                
                if os.path.exists(times_regular):
                    pdfmetrics.registerFont(TTFont('TimesVN', times_regular))
                if os.path.exists(times_bold):
                    pdfmetrics.registerFont(TTFont('TimesVN-Bold', times_bold))
                if os.path.exists(times_italic):
                    pdfmetrics.registerFont(TTFont('TimesVN-Italic', times_italic))
                
                self._fonts_registered = True
                print("✓ Đã đăng ký font Unicode (Arial, Times New Roman)")
            
        except Exception as e:
            print(f"Warning: Không thể đăng ký font Unicode: {e}")
            print("Sử dụng font mặc định Helvetica (có thể không hiển thị đúng tiếng Việt)")
    
    def _setup_styles(self):
        """Thiết lập styles cho PDF với font Unicode"""
        if self._styles_initialized:
            return
        
        self.styles = getSampleStyleSheet()
        self._styles_initialized = True
        
        # Xác định font name dựa trên việc đăng ký thành công
        main_font = 'Arial' if self._fonts_registered else 'Helvetica'
        bold_font = 'Arial-Bold' if self._fonts_registered else 'Helvetica-Bold'
        italic_font = 'Arial-Italic' if self._fonts_registered else 'Helvetica-Oblique'
        
        # Colors chuyên nghiệp
        primary_color = colors.HexColor('#1a365d')      # Dark blue
        secondary_color = colors.HexColor('#2c5282')    # Medium blue
        accent_color = colors.HexColor('#3182ce')       # Light blue
        text_color = colors.HexColor('#2d3748')         # Dark gray
        muted_color = colors.HexColor('#718096')        # Medium gray
        bg_light = colors.HexColor('#f7fafc')           # Light gray bg
        border_color = colors.HexColor('#e2e8f0')       # Border gray
        
        # Title style - Tiêu đề chính
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            fontName=bold_font,
            fontSize=26,
            leading=32,
            spaceAfter=16,
            alignment=TA_CENTER,
            textColor=primary_color
        ))
        
        # Subtitle - Phụ đề
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            fontName=main_font,
            fontSize=14,
            leading=18,
            spaceAfter=28,
            alignment=TA_CENTER,
            textColor=muted_color
        ))
        
        # Chapter title - Tiêu đề chương
        self.styles.add(ParagraphStyle(
            name='ChapterTitle',
            fontName=bold_font,
            fontSize=16,
            leading=22,
            spaceBefore=24,
            spaceAfter=14,
            textColor=secondary_color,
            borderWidth=2,
            borderColor=secondary_color,
            borderPadding=(8, 4, 8, 4),
            backColor=colors.HexColor('#ebf8ff')
        ))
        
        # Section title - Tiêu đề mục
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            fontName=bold_font,
            fontSize=13,
            leading=18,
            spaceBefore=16,
            spaceAfter=10,
            textColor=text_color,
            borderWidth=0,
            borderColor=accent_color,
            leftIndent=0
        ))
        
        # Subsection - Tiểu mục
        self.styles.add(ParagraphStyle(
            name='SubsectionTitle',
            fontName=bold_font,
            fontSize=11,
            leading=14,
            spaceBefore=12,
            spaceAfter=8,
            textColor=muted_color,
            leftIndent=10
        ))
        
        # Body text - Nội dung chính
        self.styles.add(ParagraphStyle(
            name='BodyTextVN',
            fontName=main_font,
            fontSize=10,
            leading=15,
            alignment=TA_JUSTIFY,
            spaceBefore=4,
            spaceAfter=6,
            firstLineIndent=15
        ))
        
        # Formula style - Công thức
        self.styles.add(ParagraphStyle(
            name='Formula',
            fontName=main_font,
            fontSize=11,
            leading=16,
            alignment=TA_CENTER,
            spaceBefore=10,
            spaceAfter=10,
            backColor=bg_light,
            borderWidth=1,
            borderColor=border_color,
            borderPadding=10,
            borderRadius=4
        ))
        
        # Table header - Header bảng
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            fontName=bold_font,
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.white
        ))
        
        # Table cell - Ô bảng
        self.styles.add(ParagraphStyle(
            name='TableCell',
            fontName=main_font,
            fontSize=9,
            leading=12,
            alignment=TA_LEFT
        ))
        
        # Table cell center
        self.styles.add(ParagraphStyle(
            name='TableCellCenter',
            fontName=main_font,
            fontSize=9,
            leading=12,
            alignment=TA_CENTER
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            fontName=main_font,
            fontSize=8,
            alignment=TA_CENTER,
            textColor=muted_color
        ))
        
        # Note/Warning style
        self.styles.add(ParagraphStyle(
            name='Note',
            fontName=italic_font,
            fontSize=9,
            leading=13,
            textColor=muted_color,
            leftIndent=20,
            spaceBefore=6,
            spaceAfter=6
        ))
        
        # Bullet list style
        self.styles.add(ParagraphStyle(
            name='BulletItem',
            fontName=main_font,
            fontSize=10,
            leading=14,
            leftIndent=20,
            bulletIndent=10,
            spaceBefore=3,
            spaceAfter=3
        ))
    
    def set_config(self, config: ReportConfig):
        """Thiết lập cấu hình báo cáo"""
        self.config = config
        self.labels = self.LABELS_VI if config.language == ReportLanguage.VIETNAMESE else self.LABELS_EN
    
    def add_section(self, section: ReportSection):
        """Thêm section vào báo cáo"""
        self.sections.append(section)
    
    def generate_technical_report(
        self,
        project_data: Dict[str, Any],
        calculation_results: Dict[str, Any],
        output_files: List[Dict[str, str]] = None
    ) -> str:
        """
        Tạo báo cáo kỹ thuật tổng hợp chuyên nghiệp
        
        Args:
            project_data: Thông tin dự án
            calculation_results: Kết quả tính toán chi tiết
            output_files: Danh sách file output (drawings)
            
        Returns:
            str: Đường dẫn file PDF
        """
        if not REPORTLAB_AVAILABLE:
            return self._generate_fallback_report(project_data, calculation_results)
        
        filename = f"BaoCaoKyThuat_{self.config.project_code or 'HydroDraft'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=self.config.page_size,
            topMargin=self.config.margin_top,
            bottomMargin=self.config.margin_bottom,
            leftMargin=self.config.margin_left,
            rightMargin=self.config.margin_right
        )
        
        story = []
        
        # Cover page - Trang bìa
        story.extend(self._create_cover_page())
        story.append(PageBreak())
        
        # Table of contents - Mục lục
        story.extend(self._create_table_of_contents())
        story.append(PageBreak())
        
        # Chapter 1: Project Overview - Tổng quan dự án
        story.extend(self._create_project_overview(project_data))
        story.append(PageBreak())
        
        # Chapter 2: Design Basis - Cơ sở thiết kế
        story.extend(self._create_design_basis(project_data))
        story.append(PageBreak())
        
        # Chapter 3: Calculation Results - Kết quả tính toán chi tiết
        story.extend(self._create_calculation_chapter(calculation_results))
        story.append(PageBreak())
        
        # Chapter 4: Structural Design - Thiết kế kết cấu (nếu có)
        if calculation_results.get('structural_results'):
            story.extend(self._create_structural_chapter(calculation_results))
            story.append(PageBreak())
        
        # Chapter 5: Conclusions - Kết luận
        story.extend(self._create_conclusions(calculation_results))
        
        # Appendix: Drawing Index - Phụ lục bảng kê bản vẽ
        if output_files:
            story.append(PageBreak())
            story.extend(self._create_drawing_index(output_files))
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        return filepath
    
    def _create_table_of_contents(self) -> List:
        """Tạo trang mục lục"""
        elements = []
        
        elements.append(Paragraph(self.labels["table_of_contents"], self.styles['ChapterTitle']))
        elements.append(Spacer(1, 20))
        
        # Mục lục nội dung
        toc_items = [
            ("Chương 1", "TỔNG QUAN DỰ ÁN", ""),
            ("1.1", "Giới thiệu", ""),
            ("1.2", "Vị trí công trình", ""),
            ("1.3", "Quy mô thiết kế", ""),
            ("Chương 2", "CƠ SỞ THIẾT KẾ", ""),
            ("2.1", "Tiêu chuẩn áp dụng", ""),
            ("2.2", "Điều kiện tự nhiên", ""),
            ("2.3", "Thông số đầu vào", ""),
            ("Chương 3", "KẾT QUẢ TÍNH TOÁN", ""),
            ("3.1", "Tính toán thủy lực", ""),
            ("3.2", "Tính toán kích thước", ""),
            ("3.3", "Tính toán khối lượng", ""),
            ("Chương 4", "KẾT LUẬN VÀ KIẾN NGHỊ", ""),
            ("Phụ lục", "BẢNG KÊ BẢN VẼ", ""),
        ]
        
        for num, title, page in toc_items:
            if num.startswith("Chương") or num == "Phụ lục":
                elements.append(Paragraph(
                    f"<b>{num}: {title}</b>",
                    self.styles['BodyTextVN']
                ))
            else:
                elements.append(Paragraph(
                    f"    {num}. {title}",
                    self.styles['BodyTextVN']
                ))
        
        return elements
    
    def _create_cover_page(self) -> List:
        """Tạo trang bìa chuyên nghiệp"""
        elements = []
        
        # Font names
        main_font = 'Arial' if self._fonts_registered else 'Helvetica'
        bold_font = 'Arial-Bold' if self._fonts_registered else 'Helvetica-Bold'
        
        elements.append(Spacer(1, 30))
        
        # Header - Company/Organization info
        if self.config.company_name:
            elements.append(Paragraph(
                self.config.company_name.upper(),
                ParagraphStyle(
                    'CompanyName',
                    fontName=bold_font,
                    fontSize=12,
                    alignment=TA_CENTER,
                    textColor=colors.HexColor('#2c5282')
                )
            ))
            elements.append(Spacer(1, 10))
        
        # Logo placeholder
        if self.config.logo_path and os.path.exists(self.config.logo_path):
            try:
                elements.append(Image(self.config.logo_path, width=60*mm, height=25*mm))
            except:
                pass
        
        elements.append(Spacer(1, 40))
        
        # Decorative line
        elements.append(Table(
            [['']],
            colWidths=[140*mm],
            style=TableStyle([
                ('LINEABOVE', (0, 0), (-1, 0), 3, colors.HexColor('#2c5282')),
            ])
        ))
        elements.append(Spacer(1, 20))
        
        # Main Title
        elements.append(Paragraph(self.config.title, self.styles['ReportTitle']))
        
        if self.config.subtitle:
            elements.append(Paragraph(self.config.subtitle, self.styles['ReportSubtitle']))
        
        elements.append(Spacer(1, 15))
        
        # Decorative line
        elements.append(Table(
            [['']],
            colWidths=[140*mm],
            style=TableStyle([
                ('LINEBELOW', (0, 0), (-1, 0), 3, colors.HexColor('#2c5282')),
            ])
        ))
        
        elements.append(Spacer(1, 40))
        
        # Project info table - Thông tin dự án
        project_info = [
            [f"{self.labels['project']}:", self.config.project_name or "—"],
            ["Mã dự án:", self.config.project_code or "—"],
            [f"{self.labels['client']}:", self.config.client or "—"],
            [f"{self.labels['location']}:", self.config.location or "—"],
            [f"{self.labels['date']}:", self.config.date.strftime("%d/%m/%Y")],
            [f"{self.labels['revision']}:", self.config.revision],
        ]
        
        info_table = Table(project_info, colWidths=[45*mm, 105*mm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), bold_font),
            ('FONTNAME', (1, 0), (1, -1), main_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1a202c')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(info_table)
        
        elements.append(Spacer(1, 50))
        
        # Approval block - Khối phê duyệt
        approval_header = [
            [self.labels['prepared_by'], self.labels['checked_by'], self.labels['approved_by']]
        ]
        approval_names = [
            [self.config.prepared_by or "", self.config.checked_by or "", self.config.approved_by or ""]
        ]
        approval_signature = [
            ["", "", ""]
        ]
        approval_date = [
            [f"{self.labels['date']}:", f"{self.labels['date']}:", f"{self.labels['date']}:"]
        ]
        
        approval_data = approval_header + approval_names + approval_signature + approval_date
        
        approval_table = Table(approval_data, colWidths=[50*mm, 50*mm, 50*mm], rowHeights=[20, 20, 35, 20])
        approval_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('FONTNAME', (0, 1), (-1, -1), main_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2c5282')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#a0aec0')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ebf8ff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
        ]))
        elements.append(approval_table)
        
        return elements
    
    def _create_project_overview(self, project_data: Dict) -> List:
        """Chương 1: Tổng quan dự án - Chi tiết chuyên nghiệp"""
        elements = []
        
        # Font names
        main_font = 'Arial' if self._fonts_registered else 'Helvetica'
        bold_font = 'Arial-Bold' if self._fonts_registered else 'Helvetica-Bold'
        
        elements.append(Paragraph(
            f"{self.labels['chapter']} 1: TỔNG QUAN DỰ ÁN",
            self.styles['ChapterTitle']
        ))
        
        # 1.1 Giới thiệu
        elements.append(Paragraph("1.1. Giới thiệu", self.styles['SectionTitle']))
        
        overview_text = project_data.get('description', 
            f"""Dự án "{self.config.project_name}" được thiết kế nhằm đáp ứng nhu cầu xử lý 
            nước thải/cấp nước theo các tiêu chuẩn kỹ thuật Việt Nam hiện hành. 
            Hệ thống được tính toán thiết kế với công suất phù hợp, đảm bảo 
            hiệu quả xử lý và tuân thủ các quy định về môi trường.""")
        elements.append(Paragraph(overview_text, self.styles['BodyTextVN']))
        
        # Mục tiêu dự án
        elements.append(Paragraph("Mục tiêu thiết kế:", self.styles['SubsectionTitle']))
        objectives = project_data.get('objectives', [
            "Đảm bảo công suất xử lý theo yêu cầu thiết kế",
            "Đáp ứng các tiêu chuẩn xả thải theo QCVN hiện hành",
            "Tối ưu chi phí đầu tư và vận hành",
            "Thuận tiện trong quá trình vận hành và bảo trì"
        ])
        for obj in objectives:
            elements.append(Paragraph(f"• {obj}", self.styles['BulletItem']))
        
        # 1.2 Vị trí công trình
        elements.append(Paragraph("1.2. Vị trí công trình", self.styles['SectionTitle']))
        location_info = [
            ["Địa điểm:", project_data.get('location', self.config.location) or "Không xác định"],
            ["Diện tích:", project_data.get('area', "—")],
            ["Cao độ:", project_data.get('elevation', "—")],
            ["Điều kiện địa chất:", project_data.get('geology', "Theo kết quả khảo sát")],
        ]
        
        loc_table = Table(location_info, colWidths=[50*mm, 110*mm])
        loc_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), bold_font),
            ('FONTNAME', (1, 0), (1, -1), main_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
        ]))
        elements.append(loc_table)
        elements.append(Spacer(1, 10))
        
        # 1.3 Quy mô thiết kế
        elements.append(Paragraph("1.3. Quy mô thiết kế", self.styles['SectionTitle']))
        
        if 'design_parameters' in project_data:
            params = project_data['design_parameters']
            param_data = [[self.labels['parameter'], self.labels['value'], self.labels['unit']]]
            
            for key, value in params.items():
                if isinstance(value, dict):
                    param_data.append([
                        key, 
                        str(value.get('value', '')), 
                        value.get('unit', '')
                    ])
                else:
                    param_data.append([key, str(value), ""])
            
            if len(param_data) > 1:
                param_table = Table(param_data, colWidths=[70*mm, 50*mm, 40*mm])
                param_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), bold_font),
                    ('FONTNAME', (0, 1), (-1, -1), main_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#a0aec0')),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
                ]))
                elements.append(param_table)
        else:
            # Default parameters if not provided
            default_params = [
                [self.labels['parameter'], self.labels['value'], self.labels['unit']],
                ["Lưu lượng thiết kế", "—", "m³/ngày"],
                ["Thời gian lưu nước", "—", "giờ"],
                ["Số đơn nguyên", "—", "bể"],
            ]
            param_table = Table(default_params, colWidths=[70*mm, 50*mm, 40*mm])
            param_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), bold_font),
                ('FONTNAME', (0, 1), (-1, -1), main_font),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#a0aec0')),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(param_table)
        
        return elements
    
    def _create_design_basis(self, project_data: Dict) -> List:
        """Chương 2: Cơ sở thiết kế - Chi tiết đầy đủ tiêu chuẩn"""
        elements = []
        
        # Font names
        main_font = 'Arial' if self._fonts_registered else 'Helvetica'
        bold_font = 'Arial-Bold' if self._fonts_registered else 'Helvetica-Bold'
        italic_font = 'Arial-Italic' if self._fonts_registered else 'Helvetica-Oblique'
        
        elements.append(Paragraph(
            f"{self.labels['chapter']} 2: CƠ SỞ THIẾT KẾ",
            self.styles['ChapterTitle']
        ))
        
        # 2.1 Tiêu chuẩn áp dụng
        elements.append(Paragraph("2.1. Tiêu chuẩn áp dụng", self.styles['SectionTitle']))
        
        elements.append(Paragraph(
            "Công trình được thiết kế tuân thủ các tiêu chuẩn và quy chuẩn sau:",
            self.styles['BodyTextVN']
        ))
        
        # Bảng tiêu chuẩn
        standards_data = [["Mã tiêu chuẩn", "Tên tiêu chuẩn"]]
        
        applied_standards = project_data.get('standards', list(self.TCVN_STANDARDS.keys())[:5])
        for std in applied_standards:
            if std in self.TCVN_STANDARDS:
                standards_data.append([std, self.TCVN_STANDARDS[std]])
            else:
                standards_data.append([std, ""])
        
        std_table = Table(standards_data, colWidths=[45*mm, 115*mm])
        std_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('FONTNAME', (0, 1), (-1, -1), main_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#a0aec0')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        elements.append(std_table)
        elements.append(Spacer(1, 15))
        
        # 2.2 Điều kiện tự nhiên
        elements.append(Paragraph("2.2. Điều kiện tự nhiên", self.styles['SectionTitle']))
        
        natural_conditions = project_data.get('natural_conditions', {})
        
        elements.append(Paragraph("2.2.1. Điều kiện khí hậu", self.styles['SubsectionTitle']))
        climate_text = natural_conditions.get('climate', 
            "Khu vực dự án nằm trong vùng khí hậu nhiệt đới gió mùa, có hai mùa rõ rệt: "
            "mùa mưa và mùa khô. Nhiệt độ trung bình năm khoảng 25-27°C.")
        elements.append(Paragraph(climate_text, self.styles['BodyTextVN']))
        
        elements.append(Paragraph("2.2.2. Điều kiện địa chất", self.styles['SubsectionTitle']))
        geology_text = natural_conditions.get('geology',
            "Theo kết quả khảo sát địa chất công trình, nền đất tại khu vực dự án "
            "đủ điều kiện để xây dựng công trình theo thiết kế.")
        elements.append(Paragraph(geology_text, self.styles['BodyTextVN']))
        
        elements.append(Paragraph("2.2.3. Điều kiện thủy văn", self.styles['SubsectionTitle']))
        hydrology_text = natural_conditions.get('hydrology',
            "Mực nước ngầm và điều kiện thủy văn khu vực được xem xét trong quá trình thiết kế.")
        elements.append(Paragraph(hydrology_text, self.styles['BodyTextVN']))
        
        # 2.3 Số liệu đầu vào
        elements.append(Paragraph("2.3. Số liệu đầu vào", self.styles['SectionTitle']))
        
        if 'input_data' in project_data and project_data['input_data']:
            input_data = project_data['input_data']
            input_table_data = [[self.labels['parameter'], self.labels['value'], self.labels['unit'], self.labels['note']]]
            
            for key, value in input_data.items():
                if isinstance(value, dict):
                    input_table_data.append([
                        key,
                        str(value.get('value', '')),
                        value.get('unit', ''),
                        value.get('note', '')
                    ])
                else:
                    input_table_data.append([key, str(value), '', ''])
            
            input_table = Table(input_table_data, colWidths=[50*mm, 35*mm, 30*mm, 45*mm])
            input_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), bold_font),
                ('FONTNAME', (0, 1), (-1, -1), main_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#a0aec0')),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (1, 1), (2, -1), 'CENTER'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(input_table)
        else:
            elements.append(Paragraph(
                "Số liệu đầu vào được cung cấp từ chủ đầu tư và kết quả khảo sát thực địa.",
                self.styles['BodyTextVN']
            ))
        
        return elements
    
    def _create_calculation_chapter(self, calc_results: Dict) -> List:
        """Chương 3: Tính toán thiết kế - Chi tiết với công thức"""
        elements = []
        
        # Font names
        main_font = 'Arial' if self._fonts_registered else 'Helvetica'
        bold_font = 'Arial-Bold' if self._fonts_registered else 'Helvetica-Bold'
        
        elements.append(Paragraph(
            f"{self.labels['chapter']} 3: {self.labels['calculation_results'].upper()}",
            self.styles['ChapterTitle']
        ))
        
        elements.append(Paragraph(
            "Các kết quả tính toán dưới đây được thực hiện theo các tiêu chuẩn đã nêu "
            "trong chương 2, đảm bảo độ chính xác và khả năng truy xuất nguồn gốc.",
            self.styles['BodyTextVN']
        ))
        elements.append(Spacer(1, 10))
        
        # Get calculation steps
        steps = calc_results.get('steps', [])
        
        if steps:
            for i, step in enumerate(steps, 1):
                if isinstance(step, dict):
                    elements.extend(self._format_calculation_step_detailed(i, step))
        else:
            # Fallback nếu không có steps chi tiết
            elements.extend(self._create_fallback_calculation_section(calc_results))
        
        # Final results table - Bảng tổng hợp kết quả
        if calc_results.get('final_results'):
            elements.append(Spacer(1, 15))
            elements.append(Paragraph("3.N. BẢNG TỔNG HỢP KẾT QUẢ TÍNH TOÁN", self.styles['SectionTitle']))
            
            final_data = [[self.labels['parameter'], self.labels['value'], self.labels['unit'], "Ghi chú"]]
            for key, value in calc_results['final_results'].items():
                if isinstance(value, dict):
                    final_data.append([
                        key, 
                        str(value.get('value', '')), 
                        value.get('unit', ''),
                        value.get('note', '')
                    ])
                else:
                    final_data.append([key, str(value), "", ""])
            
            final_table = Table(final_data, colWidths=[55*mm, 40*mm, 30*mm, 35*mm])
            final_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), bold_font),
                ('FONTNAME', (0, 1), (-1, -1), main_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#2c5282')),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (1, 0), (2, -1), 'CENTER'),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ebf8ff')]),
            ]))
            elements.append(final_table)
        
        return elements
    
    def _format_calculation_step_detailed(self, index: int, step: Dict) -> List:
        """Format một bước tính toán chi tiết với công thức"""
        elements = []
        
        # Font names
        main_font = 'Arial' if self._fonts_registered else 'Helvetica'
        bold_font = 'Arial-Bold' if self._fonts_registered else 'Helvetica-Bold'
        
        name = step.get('name', f'Bước {index}')
        elements.append(Paragraph(f"3.{index}. {name}", self.styles['SectionTitle']))
        
        # Description - Mô tả
        if step.get('description'):
            elements.append(Paragraph(step['description'], self.styles['BodyTextVN']))
        
        # Reference standard - Tiêu chuẩn tham chiếu
        if step.get('reference'):
            elements.append(Paragraph(
                f"<i>Theo: {step['reference']}</i>",
                self.styles['Note']
            ))
        
        # Formula box - Khung công thức
        if step.get('formula_latex') or step.get('formula_text'):
            formula_display = step.get('formula_text') or step.get('formula_latex', '')
            # Clean up LaTeX for display
            formula_clean = formula_display.replace('\\frac', '').replace('{', '(').replace('}', ')')
            formula_clean = formula_clean.replace('\\times', '×').replace('\\cdot', '·')
            formula_clean = formula_clean.replace('\\sqrt', '√').replace('\\pi', 'π')
            
            elements.append(Paragraph(
                f"<b>Công thức:</b> {formula_clean}",
                self.styles['Formula']
            ))
        
        # Inputs table - Bảng thông số đầu vào
        if step.get('inputs'):
            elements.append(Paragraph("<b>Thông số đầu vào:</b>", self.styles['BodyTextVN']))
            
            inputs = step['inputs']
            input_desc = step.get('input_descriptions', {})
            input_units = step.get('input_units', {})
            
            data = [[self.labels['parameter'], self.labels['value'], self.labels['unit'], self.labels['description']]]
            for key, value in inputs.items():
                data.append([
                    key, 
                    str(round(value, 4) if isinstance(value, float) else value), 
                    input_units.get(key, ''),
                    input_desc.get(key, '')
                ])
            
            table = Table(data, colWidths=[35*mm, 35*mm, 25*mm, 65*mm])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), bold_font),
                ('FONTNAME', (0, 1), (-1, -1), main_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#a0aec0')),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (1, 1), (2, -1), 'CENTER'),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 8))
        
        # Calculation process - Quá trình tính
        if step.get('calculation_process'):
            elements.append(Paragraph("<b>Quá trình tính:</b>", self.styles['BodyTextVN']))
            elements.append(Paragraph(step['calculation_process'], self.styles['Formula']))
        
        # Result - Kết quả
        if step.get('result') is not None:
            result = step['result']
            unit = step.get('result_unit', '')
            
            # Format result
            if isinstance(result, float):
                result_formatted = f"{result:.4f}".rstrip('0').rstrip('.')
            else:
                result_formatted = str(result)
            
            elements.append(Paragraph(
                f"<b>➡ Kết quả: {result_formatted} {unit}</b>",
                ParagraphStyle(
                    'ResultStyle',
                    fontName=bold_font,
                    fontSize=11,
                    textColor=colors.HexColor('#2c5282'),
                    spaceBefore=8,
                    spaceAfter=8,
                    backColor=colors.HexColor('#ebf8ff'),
                    borderPadding=8
                )
            ))
        
        # Status and warnings - Trạng thái và cảnh báo
        status = step.get('status', 'success')
        if status == 'warning':
            for warning in step.get('warnings', []):
                elements.append(Paragraph(
                    f"⚠️ Cảnh báo: {warning}",
                    ParagraphStyle(
                        'Warning',
                        fontName=main_font,
                        fontSize=10,
                        textColor=colors.HexColor('#c05621'),
                        backColor=colors.HexColor('#fffaf0'),
                        borderPadding=6
                    )
                ))
        elif status == 'violation':
            for error in step.get('errors', []):
                elements.append(Paragraph(
                    f"❌ Vi phạm: {error}",
                    ParagraphStyle(
                        'Error',
                        fontName=main_font,
                        fontSize=10,
                        textColor=colors.HexColor('#c53030'),
                        backColor=colors.HexColor('#fff5f5'),
                        borderPadding=6
                    )
                ))
        
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_fallback_calculation_section(self, calc_results: Dict) -> List:
        """Tạo section tính toán từ dữ liệu cơ bản"""
        elements = []
        
        # Font names
        main_font = 'Arial' if self._fonts_registered else 'Helvetica'
        bold_font = 'Arial-Bold' if self._fonts_registered else 'Helvetica-Bold'
        
        # 3.1 Tính toán thủy lực
        elements.append(Paragraph("3.1. Tính toán thủy lực", self.styles['SectionTitle']))
        
        if calc_results.get('hydraulic_results'):
            hydro = calc_results['hydraulic_results']
            
            elements.append(Paragraph(
                "Kết quả tính toán thủy lực được thực hiện theo TCVN 7957:2008:",
                self.styles['BodyTextVN']
            ))
            
            hydro_data = [[self.labels['parameter'], self.labels['value'], self.labels['unit']]]
            
            # Volume
            if 'volume' in hydro:
                vol = hydro['volume']
                if isinstance(vol, dict):
                    hydro_data.append(["Thể tích tổng", str(vol.get('total', '')), "m³"])
                    hydro_data.append(["Thể tích mỗi bể", str(vol.get('per_tank', '')), "m³"])
                else:
                    hydro_data.append(["Thể tích", str(vol), "m³"])
            
            # Other hydraulic params
            if 'retention_time' in hydro:
                hydro_data.append(["Thời gian lưu nước", str(hydro['retention_time']), "giờ"])
            if 'surface_loading' in hydro:
                hydro_data.append(["Tải trọng bề mặt", str(hydro['surface_loading']), "m³/m²/ngày"])
            if 'velocity' in hydro:
                hydro_data.append(["Vận tốc dòng chảy", str(hydro['velocity']), "m/s"])
            
            if len(hydro_data) > 1:
                hydro_table = Table(hydro_data, colWidths=[70*mm, 50*mm, 40*mm])
                hydro_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), bold_font),
                    ('FONTNAME', (0, 1), (-1, -1), main_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#a0aec0')),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('PADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(hydro_table)
        
        # 3.2 Kích thước hình học
        elements.append(Paragraph("3.2. Kích thước hình học", self.styles['SectionTitle']))
        
        if calc_results.get('dimensions'):
            dims = calc_results['dimensions']
            
            dims_data = [[self.labels['parameter'], self.labels['value'], self.labels['unit']]]
            
            if 'length' in dims:
                dims_data.append(["Chiều dài trong (L)", str(dims['length']), "m"])
            if 'width' in dims:
                dims_data.append(["Chiều rộng trong (W)", str(dims['width']), "m"])
            if 'depth' in dims:
                dims_data.append(["Chiều sâu nước (H)", str(dims['depth']), "m"])
            if 'total_depth' in dims:
                dims_data.append(["Tổng chiều sâu", str(dims['total_depth']), "m"])
            if 'wall_thickness' in dims:
                dims_data.append(["Chiều dày thành", str(dims['wall_thickness']), "m"])
            if 'number_of_tanks' in dims:
                dims_data.append(["Số đơn nguyên", str(dims['number_of_tanks']), "bể"])
            
            if len(dims_data) > 1:
                dims_table = Table(dims_data, colWidths=[70*mm, 50*mm, 40*mm])
                dims_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), bold_font),
                    ('FONTNAME', (0, 1), (-1, -1), main_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#a0aec0')),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('PADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(dims_table)
        
        # 3.3 Khối lượng vật liệu
        elements.append(Paragraph("3.3. Khối lượng vật liệu", self.styles['SectionTitle']))
        
        if calc_results.get('quantities'):
            qty = calc_results['quantities']
            
            qty_data = [["Hạng mục", "Khối lượng", self.labels['unit']]]
            
            if 'concrete' in qty:
                qty_data.append(["Bê tông", f"{qty['concrete']:.2f}", "m³"])
            if 'reinforcement' in qty:
                qty_data.append(["Thép", f"{qty['reinforcement']:.0f}", "kg"])
            if 'formwork' in qty:
                qty_data.append(["Ván khuôn", f"{qty['formwork']:.2f}", "m²"])
            if 'excavation' in qty:
                qty_data.append(["Đào đất", f"{qty['excavation']:.2f}", "m³"])
            
            if len(qty_data) > 1:
                qty_table = Table(qty_data, colWidths=[70*mm, 50*mm, 40*mm])
                qty_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), bold_font),
                    ('FONTNAME', (0, 1), (-1, -1), main_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#a0aec0')),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('PADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(qty_table)
        
        return elements
    
    def _create_structural_chapter(self, calc_results: Dict) -> List:
        """Chương thiết kế kết cấu (nếu có)"""
        elements = []
        
        elements.append(Paragraph(
            f"{self.labels['chapter']} 4: THIẾT KẾ KẾT CẤU",
            self.styles['ChapterTitle']
        ))
        
        structural = calc_results.get('structural_results', {})
        
        if structural:
            elements.append(Paragraph(
                "Thiết kế kết cấu bê tông cốt thép theo TCVN 5574:2018:",
                self.styles['BodyTextVN']
            ))
            
            # Thêm nội dung kết cấu nếu có
            for key, value in structural.items():
                elements.append(Paragraph(f"• {key}: {value}", self.styles['BulletItem']))
        
        # Bảng tổng hợp kết quả cuối cùng nếu có
        if calc_results.get('final_results'):
            elements.append(Paragraph("3.N. Bảng tổng hợp kết quả", self.styles['SectionTitle']))
            
            final_data = [["Thông số", "Giá trị", "Đơn vị"]]
            for key, value in calc_results['final_results'].items():
                if isinstance(value, dict):
                    final_data.append([key, str(value.get('value', '')), value.get('unit', '')])
                else:
                    final_data.append([key, str(value), ""])
            
            final_table = Table(final_data, colWidths=[60*mm, 50*mm, 30*mm])
            final_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(final_table)
        
        return elements
    
    def _create_conclusions(self, calc_results: Dict) -> List:
        """Chương Kết luận: Kết luận và kiến nghị chi tiết"""
        elements = []
        
        # Font names
        main_font = 'Arial' if self._fonts_registered else 'Helvetica'
        bold_font = 'Arial-Bold' if self._fonts_registered else 'Helvetica-Bold'
        
        chapter_num = "5" if calc_results.get('structural_results') else "4"
        
        elements.append(Paragraph(
            f"{self.labels['chapter']} {chapter_num}: {self.labels['conclusions'].upper()}",
            self.styles['ChapterTitle']
        ))
        
        # Kết luận chung
        elements.append(Paragraph(f"{chapter_num}.1. Kết luận", self.styles['SectionTitle']))
        
        # Check for violations
        violations = calc_results.get('violations', [])
        warnings = calc_results.get('warnings', [])
        
        if not violations:
            elements.append(Paragraph(
                "Qua quá trình tính toán thiết kế, có thể kết luận như sau:",
                self.styles['BodyTextVN']
            ))
            
            conclusions = [
                "Thiết kế đáp ứng tất cả các yêu cầu kỹ thuật theo tiêu chuẩn áp dụng.",
                "Các thông số thiết kế nằm trong giới hạn cho phép theo quy định.",
                "Công trình đảm bảo khả năng vận hành ổn định và an toàn.",
                "Khối lượng vật liệu được tính toán đầy đủ và chính xác."
            ]
            
            for c in conclusions:
                elements.append(Paragraph(f"✓ {c}", self.styles['BulletItem']))
        else:
            elements.append(Paragraph(
                "Trong quá trình tính toán, phát hiện một số vi phạm cần lưu ý:",
                self.styles['BodyTextVN']
            ))
            
            for v in violations:
                if isinstance(v, dict):
                    msg = v.get('message', 'Vi phạm không xác định')
                    severity = v.get('severity', 'warning')
                    icon = "❌" if severity == 'error' else "⚠️"
                else:
                    msg = str(v)
                    icon = "⚠️"
                
                elements.append(Paragraph(
                    f"{icon} {msg}",
                    ParagraphStyle(
                        'ViolationItem',
                        fontName=main_font,
                        fontSize=10,
                        textColor=colors.HexColor('#c53030'),
                        leftIndent=20,
                        spaceBefore=4,
                        spaceAfter=4
                    )
                ))
        
        # Cảnh báo
        if warnings:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"{chapter_num}.2. Cảnh báo", self.styles['SectionTitle']))
            
            for w in warnings:
                if isinstance(w, dict):
                    msg = w.get('message', str(w))
                else:
                    msg = str(w)
                
                elements.append(Paragraph(
                    f"⚠️ {msg}",
                    ParagraphStyle(
                        'WarningItem',
                        fontName=main_font,
                        fontSize=10,
                        textColor=colors.HexColor('#c05621'),
                        leftIndent=20,
                        spaceBefore=4,
                        spaceAfter=4
                    )
                ))
        
        # Kiến nghị
        section_num = "3" if warnings else "2"
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"{chapter_num}.{section_num}. Kiến nghị", self.styles['SectionTitle']))
        
        recommendations = [
            "Thực hiện thi công theo đúng thiết kế và quy trình được phê duyệt.",
            "Sử dụng vật liệu đúng chủng loại và chất lượng theo yêu cầu thiết kế.",
            "Kiểm tra nghiệm thu từng hạng mục trước khi tiến hành bước tiếp theo.",
            "Tuân thủ các biện pháp an toàn lao động trong quá trình thi công.",
            "Thực hiện biện pháp bảo vệ môi trường theo quy định.",
            "Bàn giao hồ sơ hoàn công và hướng dẫn vận hành cho đơn vị quản lý."
        ]
        
        for rec in recommendations:
            elements.append(Paragraph(f"• {rec}", self.styles['BulletItem']))
        
        # Chữ ký cuối báo cáo
        elements.append(Spacer(1, 40))
        
        signature_data = [
            ["", f"Ngày {self.config.date.strftime('%d')} tháng {self.config.date.strftime('%m')} năm {self.config.date.strftime('%Y')}"],
            ["", "NGƯỜI LẬP"],
            ["", ""],
            ["", ""],
            ["", self.config.prepared_by or ""]
        ]
        
        sig_table = Table(signature_data, colWidths=[90*mm, 70*mm])
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (1, 1), (1, 1), bold_font),
            ('FONTNAME', (1, 4), (1, 4), bold_font),
            ('FONTNAME', (0, 0), (0, -1), main_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(sig_table)
        
        return elements
    
    def _create_drawing_index(self, output_files: List[Dict]) -> List:
        """Phụ lục: Bảng kê bản vẽ chi tiết"""
        elements = []
        
        # Font names
        main_font = 'Arial' if self._fonts_registered else 'Helvetica'
        bold_font = 'Arial-Bold' if self._fonts_registered else 'Helvetica-Bold'
        
        elements.append(Paragraph(
            f"{self.labels['appendix']}: BẢNG KÊ BẢN VẼ",
            self.styles['ChapterTitle']
        ))
        
        elements.append(Paragraph(
            "Danh sách các bản vẽ kèm theo hồ sơ thiết kế:",
            self.styles['BodyTextVN']
        ))
        elements.append(Spacer(1, 10))
        
        # Table header
        table_data = [
            [
                "STT",
                self.labels['drawing_no'],
                self.labels['drawing_name'],
                self.labels['scale'],
                self.labels['size'],
                "Định dạng"
            ]
        ]
        
        for i, file_info in enumerate(output_files, 1):
            filename = file_info.get('name', os.path.basename(file_info.get('path', '')))
            ext = os.path.splitext(filename)[1].upper().replace('.', '')
            
            table_data.append([
                str(i),
                file_info.get('drawing_no', f"{self.config.project_code or 'HD'}-{i:02d}"),
                file_info.get('name', filename),
                file_info.get('scale', '1:100'),
                file_info.get('size', 'A1'),
                ext or 'DXF'
            ])
        
        drawing_table = Table(table_data, colWidths=[12*mm, 30*mm, 60*mm, 20*mm, 18*mm, 20*mm])
        drawing_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('FONTNAME', (0, 1), (-1, -1), main_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#2c5282')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (3, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        elements.append(drawing_table)
        
        # Note
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(
            "<i>Ghi chú: Các bản vẽ được xuất ở định dạng DXF tương thích với AutoCAD 2018 trở lên.</i>",
            self.styles['Note']
        ))
        
        return elements
    
    def _add_header_footer(self, canvas, doc):
        """Thêm header và footer chuyên nghiệp cho mỗi trang"""
        canvas.saveState()
        
        # Font
        font_name = 'Arial' if self._fonts_registered else 'Helvetica'
        bold_font = 'Arial-Bold' if self._fonts_registered else 'Helvetica-Bold'
        
        page_width = self.config.page_size[0]
        page_height = self.config.page_size[1]
        
        # Header line
        canvas.setStrokeColor(colors.HexColor('#2c5282'))
        canvas.setLineWidth(1.5)
        canvas.line(
            self.config.margin_left,
            page_height - 18*mm,
            page_width - self.config.margin_right,
            page_height - 18*mm
        )
        
        # Header text - left
        canvas.setFont(font_name, 8)
        canvas.setFillColor(colors.HexColor('#4a5568'))
        canvas.drawString(
            self.config.margin_left,
            page_height - 14*mm,
            f"{self.config.project_name}"
        )
        
        # Header text - right
        canvas.drawRightString(
            page_width - self.config.margin_right,
            page_height - 14*mm,
            f"{self.config.title}"
        )
        
        # Footer line
        canvas.setLineWidth(0.5)
        canvas.setStrokeColor(colors.HexColor('#a0aec0'))
        canvas.line(
            self.config.margin_left,
            22*mm,
            page_width - self.config.margin_right,
            22*mm
        )
        
        # Footer - left: company
        canvas.setFont(font_name, 7)
        canvas.setFillColor(colors.HexColor('#718096'))
        canvas.drawString(
            self.config.margin_left,
            17*mm,
            "HydroDraft - Professional Engineering Platform"
        )
        
        # Footer - center: page number
        canvas.setFont(bold_font, 9)
        canvas.setFillColor(colors.HexColor('#2c5282'))
        canvas.drawCentredString(
            page_width / 2,
            17*mm,
            f"Trang {doc.page}"
        )
        
        # Footer - right: revision and date
        canvas.setFont(font_name, 7)
        canvas.setFillColor(colors.HexColor('#718096'))
        canvas.drawRightString(
            page_width - self.config.margin_right,
            17*mm,
            f"{self.config.revision} | {self.config.date.strftime('%d/%m/%Y')}"
        )
        
        canvas.restoreState()
    
    def _generate_fallback_report(
        self,
        project_data: Dict,
        calc_results: Dict
    ) -> str:
        """Tạo báo cáo text khi không có reportlab"""
        filename = f"technical_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"  {self.config.title}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Dự án: {self.config.project_name}\n")
            f.write(f"Chủ đầu tư: {self.config.client}\n")
            f.write(f"Địa điểm: {self.config.location}\n")
            f.write(f"Ngày: {self.config.date.strftime('%d/%m/%Y')}\n")
            f.write(f"Phiên bản: {self.config.revision}\n\n")
            
            f.write("-" * 60 + "\n")
            f.write("KẾT QUẢ TÍNH TOÁN\n")
            f.write("-" * 60 + "\n\n")
            
            f.write(json.dumps(calc_results, indent=2, ensure_ascii=False))
        
        return filepath
    
    def generate_calculation_appendix(
        self,
        calculation_log: Dict[str, Any]
    ) -> str:
        """
        Tạo phụ lục tính toán chi tiết
        
        Args:
            calculation_log: Log tính toán từ calculation engine
            
        Returns:
            str: Đường dẫn file PDF
        """
        if not REPORTLAB_AVAILABLE:
            return self._generate_fallback_report({}, calculation_log)
        
        filename = f"calculation_appendix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=self.config.page_size,
            topMargin=self.config.margin_top,
            bottomMargin=self.config.margin_bottom,
            leftMargin=self.config.margin_left,
            rightMargin=self.config.margin_right
        )
        
        story = []
        
        # Title
        story.append(Paragraph("PHỤ LỤC TÍNH TOÁN", self.styles['ReportTitle']))
        story.append(Paragraph(
            f"Dự án: {self.config.project_name}",
            self.styles['ReportSubtitle']
        ))
        story.append(Spacer(1, 20))
        
        # Calculation steps
        steps = calculation_log.get('steps', [])
        for i, step in enumerate(steps, 1):
            if isinstance(step, dict):
                story.extend(self._format_calculation_step(i, step))
        
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        return filepath
    
    def _format_calculation_step(self, index: int, step: Dict) -> List:
        """Format một bước tính toán"""
        elements = []
        
        name = step.get('name', f'Bước {index}')
        elements.append(Paragraph(f"{index}. {name}", self.styles['SectionTitle']))
        
        # Description
        if step.get('description'):
            elements.append(Paragraph(step['description'], self.styles['BodyText']))
        
        # Formula box
        if step.get('formula_latex') or step.get('formula_text'):
            formula = step.get('formula_text') or step.get('formula_latex', '')
            elements.append(Paragraph(formula, self.styles['Formula']))
        
        # Inputs table
        if step.get('inputs'):
            inputs = step['inputs']
            input_desc = step.get('input_descriptions', {})
            
            data = [["Ký hiệu", "Giá trị", "Mô tả"]]
            for key, value in inputs.items():
                data.append([key, str(value), input_desc.get(key, '')])
            
            table = Table(data, colWidths=[30*mm, 40*mm, 70*mm])
            table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(table)
        
        # Result
        if step.get('result') is not None:
            result = step['result']
            unit = step.get('result_unit', '')
            formatted = step.get('result_formatted', f"{result} {unit}")
            elements.append(Paragraph(
                f"<b>➡ Kết quả: {formatted}</b>",
                self.styles['BodyText']
            ))
        
        # Reference
        if step.get('reference'):
            elements.append(Paragraph(
                f"<i>Tham chiếu: {step['reference']}</i>",
                self.styles['BodyText']
            ))
        
        # Status and warnings
        status = step.get('status', 'success')
        if status == 'warning':
            for warning in step.get('warnings', []):
                elements.append(Paragraph(
                    f"⚠️ {warning}",
                    self.styles['BodyText']
                ))
        elif status == 'violation':
            for error in step.get('errors', []):
                elements.append(Paragraph(
                    f"❌ {error}",
                    self.styles['BodyText']
                ))
        
        elements.append(Spacer(1, 10))
        
        return elements


# Factory function
def create_pdf_generator(output_dir: str = None) -> PDFReportGenerator:
    """Create PDF generator instance"""
    return PDFReportGenerator(output_dir or "./outputs/reports")
