"""
CAD Drawing Validation Engine - Kiểm tra chất lượng bản vẽ

SPRINT 3: PROFESSIONAL CAD
Validation Engine kiểm tra:
- Missing dimensions (thiếu kích thước)
- Missing annotations (thiếu ghi chú)
- Scale consistency (nhất quán tỷ lệ)
- Layer standards (tiêu chuẩn layer)
- Block completeness (đầy đủ block)
- Text/Dim style compliance

Block export if incomplete - Chặn xuất bản vẽ không đạt
"""

import ezdxf
from ezdxf.entities import DXFEntity
from typing import Dict, Any, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import math


class ValidationSeverity(Enum):
    """Mức độ nghiêm trọng của lỗi"""
    INFO = "INFO"           # Thông tin
    WARNING = "WARNING"     # Cảnh báo
    ERROR = "ERROR"         # Lỗi (chặn xuất)
    CRITICAL = "CRITICAL"   # Nghiêm trọng (chặn xuất)


class ValidationCategory(Enum):
    """Loại kiểm tra"""
    DIMENSION = "DIMENSION"
    ANNOTATION = "ANNOTATION"
    LAYER = "LAYER"
    SCALE = "SCALE"
    BLOCK = "BLOCK"
    TEXT_STYLE = "TEXT_STYLE"
    DIM_STYLE = "DIM_STYLE"
    GEOMETRY = "GEOMETRY"
    COMPLETENESS = "COMPLETENESS"


@dataclass
class ValidationIssue:
    """Chi tiết lỗi kiểm tra"""
    code: str
    message: str
    category: ValidationCategory
    severity: ValidationSeverity
    location: Optional[Tuple[float, float]] = None
    entity_handle: Optional[str] = None
    suggestion: str = ""
    reference: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "code": self.code,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "location": self.location,
            "entity_handle": self.entity_handle,
            "suggestion": self.suggestion,
            "reference": self.reference
        }


@dataclass
class ValidationResult:
    """Kết quả validation tổng hợp"""
    is_valid: bool
    can_export: bool
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues_by_category: Dict[str, int]
    issues: List[ValidationIssue]
    validation_time: str
    drawing_stats: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "is_valid": self.is_valid,
            "can_export": self.can_export,
            "total_issues": self.total_issues,
            "issues_by_severity": self.issues_by_severity,
            "issues_by_category": self.issues_by_category,
            "issues": [i.to_dict() for i in self.issues],
            "validation_time": self.validation_time,
            "drawing_stats": self.drawing_stats
        }


class CADValidationEngine:
    """
    Engine kiểm tra chất lượng bản vẽ CAD
    
    Kiểm tra:
    1. Dimensions - Đủ kích thước cần thiết
    2. Annotations - Đủ ghi chú, tiêu đề
    3. Layers - Đúng layer tiêu chuẩn
    4. Scale - Nhất quán tỷ lệ
    5. Blocks - Hoàn chỉnh attributes
    6. Styles - Đúng text/dim style
    """
    
    # Required layers for different drawing types
    REQUIRED_LAYERS = {
        "tank": ["STR_WALL", "STR_FOUNDATION", "ANNO_DIM", "ANNO_TEXT"],
        "pipe": ["PIPE_MAIN", "STRUCT_MH", "ANNO_DIM", "ANNO_TEXT"],
        "well": ["PIPE_MAIN", "STR_WALL", "HATCH_CONCRETE", "ANNO_DIM", "ANNO_TEXT"],
        "general": ["ANNO_DIM", "ANNO_TEXT"]
    }
    
    # Minimum dimension requirements
    MIN_DIMENSIONS = {
        "tank_plan": 4,      # L, W inside + outside
        "tank_section": 6,   # H, depth, thickness, etc.
        "pipe_profile": 3,   # Length, slope, diameter
        "well_section": 5,   # Depth, diameters, levels
    }
    
    # Required text elements
    REQUIRED_TEXTS = {
        "tank_plan": ["title", "scale"],
        "tank_section": ["title", "scale", "elevation"],
        "pipe_profile": ["title", "scale", "station"],
        "general": ["title"]
    }
    
    def __init__(self, doc):
        self.doc = doc
        self.msp = doc.modelspace()
        self.issues: List[ValidationIssue] = []
    
    def validate_all(self, drawing_type: str = "general") -> ValidationResult:
        """
        Chạy tất cả validation
        
        Args:
            drawing_type: "tank" | "pipe" | "well" | "general"
        """
        self.issues = []
        start_time = datetime.now()
        
        # Run all validations
        self._validate_layers(drawing_type)
        self._validate_dimensions(drawing_type)
        self._validate_annotations(drawing_type)
        self._validate_text_styles()
        self._validate_dim_styles()
        self._validate_blocks()
        self._validate_scale_consistency()
        self._validate_geometry()
        self._validate_completeness(drawing_type)
        
        # Collect stats
        stats = self._collect_drawing_stats()
        
        # Count by severity
        severity_counts = {s.value: 0 for s in ValidationSeverity}
        for issue in self.issues:
            severity_counts[issue.severity.value] += 1
        
        # Count by category
        category_counts = {c.value: 0 for c in ValidationCategory}
        for issue in self.issues:
            category_counts[issue.category.value] += 1
        
        # Determine if export is allowed
        blocking_count = severity_counts.get("ERROR", 0) + severity_counts.get("CRITICAL", 0)
        can_export = blocking_count == 0
        is_valid = len(self.issues) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            can_export=can_export,
            total_issues=len(self.issues),
            issues_by_severity=severity_counts,
            issues_by_category=category_counts,
            issues=self.issues,
            validation_time=datetime.now().isoformat(),
            drawing_stats=stats
        )
    
    def _add_issue(
        self,
        code: str,
        message: str,
        category: ValidationCategory,
        severity: ValidationSeverity,
        location: Tuple[float, float] = None,
        entity_handle: str = None,
        suggestion: str = "",
        reference: str = ""
    ):
        """Thêm issue vào danh sách"""
        self.issues.append(ValidationIssue(
            code=code,
            message=message,
            category=category,
            severity=severity,
            location=location,
            entity_handle=entity_handle,
            suggestion=suggestion,
            reference=reference
        ))
    
    # ==========================================
    # LAYER VALIDATION
    # ==========================================
    
    def _validate_layers(self, drawing_type: str):
        """Kiểm tra layer"""
        existing_layers = set(self.doc.layers.entries.keys())
        required = self.REQUIRED_LAYERS.get(drawing_type, self.REQUIRED_LAYERS["general"])
        
        # Check required layers exist
        for layer_name in required:
            if layer_name not in existing_layers:
                self._add_issue(
                    code="LAY001",
                    message=f"Thiếu layer bắt buộc: {layer_name}",
                    category=ValidationCategory.LAYER,
                    severity=ValidationSeverity.ERROR,
                    suggestion=f"Thêm layer {layer_name} vào bản vẽ",
                    reference="TCVN 8-1:2002"
                )
        
        # Check for entities on layer 0
        layer_0_count = 0
        for entity in self.msp:
            if hasattr(entity.dxf, 'layer') and entity.dxf.layer == "0":
                layer_0_count += 1
        
        if layer_0_count > 10:
            self._add_issue(
                code="LAY002",
                message=f"Có {layer_0_count} đối tượng trên Layer 0 (nên phân layer)",
                category=ValidationCategory.LAYER,
                severity=ValidationSeverity.WARNING,
                suggestion="Di chuyển đối tượng sang layer phù hợp"
            )
        
        # Check layer colors
        for layer in self.doc.layers:
            if layer.dxf.name.startswith("_"):
                continue
            if layer.color == 256:  # ByLayer but no color set
                self._add_issue(
                    code="LAY003",
                    message=f"Layer {layer.dxf.name} chưa gán màu",
                    category=ValidationCategory.LAYER,
                    severity=ValidationSeverity.INFO,
                    suggestion="Gán màu cho layer"
                )
    
    # ==========================================
    # DIMENSION VALIDATION
    # ==========================================
    
    def _validate_dimensions(self, drawing_type: str):
        """Kiểm tra kích thước"""
        # Count dimensions
        dim_count = 0
        dim_types = {"linear": 0, "aligned": 0, "radius": 0, "diameter": 0, "angular": 0}
        
        for entity in self.msp:
            if entity.dxftype() == "DIMENSION":
                dim_count += 1
                dim_type = entity.dxf.dimtype
                if dim_type == 0:
                    dim_types["linear"] += 1
                elif dim_type == 1:
                    dim_types["aligned"] += 1
                elif dim_type == 4:
                    dim_types["radius"] += 1
                elif dim_type == 3:
                    dim_types["diameter"] += 1
                elif dim_type == 2:
                    dim_types["angular"] += 1
        
        # Check minimum dimension count
        min_required = self.MIN_DIMENSIONS.get(f"{drawing_type}_plan", 
                                                self.MIN_DIMENSIONS.get(f"{drawing_type}_section", 2))
        
        if dim_count < min_required:
            self._add_issue(
                code="DIM001",
                message=f"Thiếu kích thước: có {dim_count}, yêu cầu tối thiểu {min_required}",
                category=ValidationCategory.DIMENSION,
                severity=ValidationSeverity.ERROR,
                suggestion="Thêm các kích thước còn thiếu",
                reference="TCVN 8-24:2002"
            )
        
        # Check for zero-value dimensions
        for entity in self.msp:
            if entity.dxftype() == "DIMENSION":
                try:
                    # Check measurement
                    if hasattr(entity, 'get_measurement'):
                        value = entity.get_measurement()
                        if value is not None and abs(value) < 0.0001:
                            self._add_issue(
                                code="DIM002",
                                message="Phát hiện kích thước bằng 0",
                                category=ValidationCategory.DIMENSION,
                                severity=ValidationSeverity.WARNING,
                                entity_handle=entity.dxf.handle,
                                suggestion="Kiểm tra lại điểm đo kích thước"
                            )
                except:
                    pass
    
    # ==========================================
    # ANNOTATION VALIDATION
    # ==========================================
    
    def _validate_annotations(self, drawing_type: str):
        """Kiểm tra ghi chú"""
        # Collect all text content
        texts = []
        text_entities = []
        
        for entity in self.msp:
            if entity.dxftype() in ("TEXT", "MTEXT"):
                content = ""
                if entity.dxftype() == "TEXT":
                    content = entity.dxf.text
                else:
                    content = entity.text
                
                texts.append(content.lower() if content else "")
                text_entities.append(entity)
        
        required_texts = self.REQUIRED_TEXTS.get(drawing_type, self.REQUIRED_TEXTS["general"])
        
        # Check for title
        if "title" in required_texts:
            has_title = any("mặt" in t or "plan" in t or "section" in t or 
                          "bằng" in t or "cắt" in t or "chi tiết" in t 
                          for t in texts)
            if not has_title:
                self._add_issue(
                    code="ANN001",
                    message="Thiếu tiêu đề bản vẽ",
                    category=ValidationCategory.ANNOTATION,
                    severity=ValidationSeverity.ERROR,
                    suggestion="Thêm tiêu đề: MẶT BẰNG, MẶT CẮT, etc."
                )
        
        # Check for scale notation
        if "scale" in required_texts:
            has_scale = any("1:" in t or "tỷ lệ" in t or "scale" in t for t in texts)
            if not has_scale:
                self._add_issue(
                    code="ANN002",
                    message="Thiếu ghi chú tỷ lệ",
                    category=ValidationCategory.ANNOTATION,
                    severity=ValidationSeverity.WARNING,
                    suggestion="Thêm ghi chú tỷ lệ: TỶ LỆ 1:100"
                )
        
        # Check for elevation marks
        if "elevation" in required_texts:
            has_elevation = any("+" in t or "-" in t or "cao độ" in t for t in texts)
            if not has_elevation:
                self._add_issue(
                    code="ANN003",
                    message="Thiếu ghi chú cao độ",
                    category=ValidationCategory.ANNOTATION,
                    severity=ValidationSeverity.WARNING,
                    suggestion="Thêm các mốc cao độ"
                )
        
        # Check for empty texts
        for entity in text_entities:
            content = entity.dxf.text if entity.dxftype() == "TEXT" else entity.text
            if not content or content.strip() == "":
                self._add_issue(
                    code="ANN004",
                    message="Phát hiện text rỗng",
                    category=ValidationCategory.ANNOTATION,
                    severity=ValidationSeverity.INFO,
                    entity_handle=entity.dxf.handle,
                    suggestion="Xóa hoặc điền nội dung text"
                )
    
    # ==========================================
    # TEXT STYLE VALIDATION
    # ==========================================
    
    def _validate_text_styles(self):
        """Kiểm tra text style"""
        used_styles = set()
        
        for entity in self.msp:
            if entity.dxftype() in ("TEXT", "MTEXT"):
                style = entity.dxf.style if hasattr(entity.dxf, 'style') else "Standard"
                used_styles.add(style)
        
        # Check for Standard style (should use custom styles)
        if "Standard" in used_styles:
            self._add_issue(
                code="TXT001",
                message="Đang sử dụng text style 'Standard' (nên dùng style tùy chỉnh)",
                category=ValidationCategory.TEXT_STYLE,
                severity=ValidationSeverity.INFO,
                suggestion="Sử dụng STANDARD_VN, ENGINEERING, hoặc style tùy chỉnh"
            )
        
        # Check text heights
        heights = []
        for entity in self.msp:
            if entity.dxftype() == "TEXT":
                heights.append(entity.dxf.height)
        
        if heights:
            unique_heights = set(heights)
            if len(unique_heights) > 5:
                self._add_issue(
                    code="TXT002",
                    message=f"Quá nhiều kích thước text khác nhau ({len(unique_heights)} loại)",
                    category=ValidationCategory.TEXT_STYLE,
                    severity=ValidationSeverity.WARNING,
                    suggestion="Chuẩn hóa chiều cao text theo tỷ lệ bản vẽ"
                )
    
    # ==========================================
    # DIMENSION STYLE VALIDATION
    # ==========================================
    
    def _validate_dim_styles(self):
        """Kiểm tra dimension style"""
        used_dimstyles = set()
        
        for entity in self.msp:
            if entity.dxftype() == "DIMENSION":
                dimstyle = entity.dxf.dimstyle if hasattr(entity.dxf, 'dimstyle') else "Standard"
                used_dimstyles.add(dimstyle)
        
        # Check for Standard style
        if "Standard" in used_dimstyles:
            self._add_issue(
                code="DMS001",
                message="Đang sử dụng dim style 'Standard'",
                category=ValidationCategory.DIM_STYLE,
                severity=ValidationSeverity.INFO,
                suggestion="Sử dụng DIM_1_100 hoặc dimstyle theo tỷ lệ"
            )
        
        # Check for multiple dimstyles (inconsistency)
        if len(used_dimstyles) > 2:
            self._add_issue(
                code="DMS002",
                message=f"Sử dụng nhiều dim style ({len(used_dimstyles)} loại)",
                category=ValidationCategory.DIM_STYLE,
                severity=ValidationSeverity.WARNING,
                suggestion="Chuẩn hóa về một dim style cho toàn bản vẽ"
            )
    
    # ==========================================
    # BLOCK VALIDATION
    # ==========================================
    
    def _validate_blocks(self):
        """Kiểm tra block"""
        block_refs = []
        
        for entity in self.msp:
            if entity.dxftype() == "INSERT":
                block_refs.append(entity)
        
        # Check for blocks without attributes
        for block_ref in block_refs:
            block_name = block_ref.dxf.name
            
            # Get block definition
            if block_name in self.doc.blocks:
                block_def = self.doc.blocks[block_name]
                attdefs = list(block_def.query('ATTDEF'))
                
                if attdefs:
                    # Check if all attributes are filled
                    attribs = list(block_ref.attribs)
                    attrib_tags = {a.dxf.tag for a in attribs}
                    attdef_tags = {a.dxf.tag for a in attdefs}
                    
                    missing = attdef_tags - attrib_tags
                    if missing:
                        self._add_issue(
                            code="BLK001",
                            message=f"Block {block_name} thiếu thuộc tính: {missing}",
                            category=ValidationCategory.BLOCK,
                            severity=ValidationSeverity.WARNING,
                            entity_handle=block_ref.dxf.handle,
                            suggestion="Điền đầy đủ thuộc tính block"
                        )
                    
                    # Check for empty attributes
                    for attrib in attribs:
                        if not attrib.dxf.text or attrib.dxf.text.strip() == "":
                            self._add_issue(
                                code="BLK002",
                                message=f"Block {block_name} có thuộc tính rỗng: {attrib.dxf.tag}",
                                category=ValidationCategory.BLOCK,
                                severity=ValidationSeverity.INFO,
                                entity_handle=block_ref.dxf.handle
                            )
    
    # ==========================================
    # SCALE CONSISTENCY VALIDATION
    # ==========================================
    
    def _validate_scale_consistency(self):
        """Kiểm tra nhất quán tỷ lệ"""
        # Analyze text heights to detect scale
        text_heights = []
        for entity in self.msp:
            if entity.dxftype() == "TEXT":
                text_heights.append(entity.dxf.height)
        
        if text_heights:
            min_h = min(text_heights)
            max_h = max(text_heights)
            
            # If height ratio > 10, likely mixed scales
            if max_h / min_h > 10:
                self._add_issue(
                    code="SCL001",
                    message=f"Phát hiện tỷ lệ text không nhất quán (min={min_h:.3f}, max={max_h:.3f})",
                    category=ValidationCategory.SCALE,
                    severity=ValidationSeverity.WARNING,
                    suggestion="Kiểm tra và chuẩn hóa chiều cao text theo tỷ lệ"
                )
        
        # Check block scales
        block_scales = []
        for entity in self.msp:
            if entity.dxftype() == "INSERT":
                xscale = entity.dxf.xscale
                yscale = entity.dxf.yscale
                block_scales.append((xscale, yscale))
                
                # Non-uniform scale
                if abs(xscale - yscale) > 0.001:
                    self._add_issue(
                        code="SCL002",
                        message=f"Block {entity.dxf.name} có tỷ lệ X/Y không đều ({xscale}/{yscale})",
                        category=ValidationCategory.SCALE,
                        severity=ValidationSeverity.WARNING,
                        entity_handle=entity.dxf.handle,
                        suggestion="Chỉnh tỷ lệ X = Y cho block"
                    )
    
    # ==========================================
    # GEOMETRY VALIDATION
    # ==========================================
    
    def _validate_geometry(self):
        """Kiểm tra hình học"""
        # Check for zero-length lines
        zero_lines = 0
        for entity in self.msp:
            if entity.dxftype() == "LINE":
                start = entity.dxf.start
                end = entity.dxf.end
                length = math.sqrt(
                    (end.x - start.x)**2 + 
                    (end.y - start.y)**2 + 
                    (end.z - start.z)**2
                )
                if length < 0.0001:
                    zero_lines += 1
        
        if zero_lines > 0:
            self._add_issue(
                code="GEO001",
                message=f"Có {zero_lines} đường có chiều dài = 0",
                category=ValidationCategory.GEOMETRY,
                severity=ValidationSeverity.INFO,
                suggestion="Xóa các đường có chiều dài = 0"
            )
        
        # Check for very small circles
        small_circles = 0
        for entity in self.msp:
            if entity.dxftype() == "CIRCLE":
                if entity.dxf.radius < 0.0001:
                    small_circles += 1
        
        if small_circles > 0:
            self._add_issue(
                code="GEO002",
                message=f"Có {small_circles} đường tròn có bán kính rất nhỏ",
                category=ValidationCategory.GEOMETRY,
                severity=ValidationSeverity.INFO
            )
    
    # ==========================================
    # COMPLETENESS VALIDATION
    # ==========================================
    
    def _validate_completeness(self, drawing_type: str):
        """Kiểm tra hoàn chỉnh"""
        # Check for empty modelspace
        entity_count = len(list(self.msp))
        if entity_count < 10:
            self._add_issue(
                code="CMP001",
                message=f"Bản vẽ có ít đối tượng ({entity_count})",
                category=ValidationCategory.COMPLETENESS,
                severity=ValidationSeverity.WARNING,
                suggestion="Bản vẽ có thể chưa hoàn chỉnh"
            )
        
        # Check for specific drawing type requirements
        if drawing_type == "tank":
            # Tank should have hatch
            has_hatch = any(e.dxftype() == "HATCH" for e in self.msp)
            if not has_hatch:
                self._add_issue(
                    code="CMP002",
                    message="Bản vẽ bể thiếu hatch (mặt cắt vật liệu)",
                    category=ValidationCategory.COMPLETENESS,
                    severity=ValidationSeverity.WARNING,
                    suggestion="Thêm hatch bê tông cho mặt cắt"
                )
        
        elif drawing_type == "pipe":
            # Pipe should have profile table or manhole data
            has_table_like = False
            line_count = sum(1 for e in self.msp if e.dxftype() == "LINE")
            if line_count > 20:
                has_table_like = True
            
            if not has_table_like:
                self._add_issue(
                    code="CMP003",
                    message="Trắc dọc có thể thiếu bảng thông số",
                    category=ValidationCategory.COMPLETENESS,
                    severity=ValidationSeverity.INFO
                )
    
    # ==========================================
    # STATISTICS
    # ==========================================
    
    def _collect_drawing_stats(self) -> Dict[str, Any]:
        """Thu thập thống kê bản vẽ"""
        stats = {
            "total_entities": 0,
            "entities_by_type": {},
            "layers_used": set(),
            "blocks_used": set(),
            "text_count": 0,
            "dimension_count": 0,
            "hatch_count": 0
        }
        
        for entity in self.msp:
            stats["total_entities"] += 1
            
            etype = entity.dxftype()
            stats["entities_by_type"][etype] = stats["entities_by_type"].get(etype, 0) + 1
            
            if hasattr(entity.dxf, 'layer'):
                stats["layers_used"].add(entity.dxf.layer)
            
            if etype == "INSERT":
                stats["blocks_used"].add(entity.dxf.name)
            elif etype in ("TEXT", "MTEXT"):
                stats["text_count"] += 1
            elif etype == "DIMENSION":
                stats["dimension_count"] += 1
            elif etype == "HATCH":
                stats["hatch_count"] += 1
        
        # Convert sets to lists for JSON
        stats["layers_used"] = list(stats["layers_used"])
        stats["blocks_used"] = list(stats["blocks_used"])
        
        return stats


class DrawingExportGuard:
    """
    Guard để kiểm tra trước khi xuất bản vẽ
    
    Sử dụng:
        guard = DrawingExportGuard(doc)
        result = guard.check_can_export("tank")
        if result.can_export:
            doc.saveas(...)
        else:
            print(result.blocking_issues)
    """
    
    def __init__(self, doc):
        self.doc = doc
        self.validator = CADValidationEngine(doc)
    
    def check_can_export(self, drawing_type: str = "general") -> ValidationResult:
        """
        Kiểm tra có thể xuất bản vẽ không
        
        Returns:
            ValidationResult với can_export = True/False
        """
        return self.validator.validate_all(drawing_type)
    
    def get_blocking_issues(self, result: ValidationResult) -> List[ValidationIssue]:
        """Lấy danh sách lỗi chặn xuất"""
        return [
            issue for issue in result.issues
            if issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
        ]
    
    def export_with_validation(
        self,
        filepath: str,
        drawing_type: str = "general",
        force: bool = False
    ) -> Tuple[bool, ValidationResult]:
        """
        Xuất bản vẽ với validation
        
        Args:
            filepath: Đường dẫn file
            drawing_type: Loại bản vẽ
            force: Bỏ qua lỗi và xuất
            
        Returns:
            (success, validation_result)
        """
        result = self.check_can_export(drawing_type)
        
        if result.can_export or force:
            self.doc.saveas(filepath)
            return True, result
        else:
            return False, result


def validate_drawing(doc, drawing_type: str = "general") -> ValidationResult:
    """Hàm tiện ích validate bản vẽ"""
    validator = CADValidationEngine(doc)
    return validator.validate_all(drawing_type)
