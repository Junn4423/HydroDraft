"""
Template Manager - Quản lý thư viện mẫu thiết kế
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


class TemplateManager:
    """
    Quản lý thư viện mẫu thiết kế
    
    Chức năng:
    - Load template từ file JSON
    - Validate input với template
    - Apply default values
    - Get design parameters
    """
    
    def __init__(self, template_dir: str = None):
        if template_dir is None:
            # Thư mục templates chính là thư mục chứa file này
            current_dir = Path(__file__).parent
            template_dir = current_dir
        
        self.template_dir = Path(template_dir)
        self.templates: Dict[str, Dict] = {}
        self._load_all_templates()
    
    def _load_all_templates(self) -> None:
        """Load tất cả templates từ thư mục"""
        if not self.template_dir.exists():
            print(f"Warning: templates directory does not exist: {self.template_dir}")
            return
        
        for file_path in self.template_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                    template_id = template.get("template_id", file_path.stem)
                    self.templates[template_id] = template
                    print(f"Loaded template: {template_id}")
            except Exception as e:
                print(f"Error loading template {file_path}: {e}")
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """
        Lấy template theo ID
        
        Args:
            template_id: ID của template
            
        Returns:
            Dict template hoặc None
        """
        return self.templates.get(template_id)
    
    def get_templates_by_category(self, category: str) -> List[Dict]:
        """
        Lấy danh sách templates theo category
        
        Args:
            category: Loại template (sedimentation, biological, drainage, ...)
            
        Returns:
            List các templates
        """
        return [
            t for t in self.templates.values()
            if t.get("category") == category
        ]
    
    def list_templates(self) -> List[Dict[str, str]]:
        """
        Liệt kê tất cả templates
        
        Returns:
            List các template info
        """
        return [
            {
                "id": t.get("template_id"),
                "name": t.get("name"),
                "category": t.get("category"),
                "description": t.get("description")
            }
            for t in self.templates.values()
        ]
    
    def get_parameters(self, template_id: str) -> Optional[Dict]:
        """
        Lấy danh sách parameters của template
        
        Args:
            template_id: ID của template
            
        Returns:
            Dict parameters
        """
        template = self.get_template(template_id)
        if template:
            return template.get("parameters", {})
        return None
    
    def get_default_values(self, template_id: str) -> Dict[str, Any]:
        """
        Lấy giá trị mặc định của tất cả parameters
        
        Args:
            template_id: ID của template
            
        Returns:
            Dict {param_name: default_value}
        """
        params = self.get_parameters(template_id)
        if not params:
            return {}
        
        defaults = {}
        for name, config in params.items():
            if "default" in config:
                defaults[name] = config["default"]
            elif "min" in config:
                defaults[name] = config["min"]
        
        return defaults
    
    def validate_input(
        self,
        template_id: str,
        input_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate input values với template constraints
        
        Args:
            template_id: ID của template
            input_values: Dict các giá trị đầu vào
            
        Returns:
            Dict {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str],
                "adjusted_values": Dict
            }
        """
        template = self.get_template(template_id)
        if not template:
            return {
                "valid": False,
                "errors": [f"Template không tồn tại: {template_id}"],
                "warnings": [],
                "adjusted_values": {}
            }
        
        params = template.get("parameters", {})
        errors = []
        warnings = []
        adjusted = {}
        
        for name, config in params.items():
            value = input_values.get(name)
            
            # Kiểm tra required
            if value is None:
                if "default" in config:
                    adjusted[name] = config["default"]
                    warnings.append(f"{name}: Sử dụng giá trị mặc định {config['default']}")
                elif "min" in config:
                    adjusted[name] = config["min"]
                    warnings.append(f"{name}: Sử dụng giá trị tối thiểu {config['min']}")
                continue
            
            # Validate theo type
            if config.get("type") == "enum":
                options = config.get("options", [])
                if value not in options:
                    errors.append(f"{name}: Giá trị '{value}' không hợp lệ. Chọn: {options}")
                    adjusted[name] = config.get("default", options[0])
                else:
                    adjusted[name] = value
                continue
            
            # Validate min/max
            min_val = config.get("min")
            max_val = config.get("max")
            
            if min_val is not None and value < min_val:
                errors.append(f"{name}: Giá trị {value} < min {min_val}")
                adjusted[name] = min_val
            elif max_val is not None and value > max_val:
                errors.append(f"{name}: Giá trị {value} > max {max_val}")
                adjusted[name] = max_val
            else:
                adjusted[name] = value
            
            # Kiểm tra typical range (warning only)
            typical = config.get("typical_range")
            if typical and (value < typical[0] or value > typical[1]):
                warnings.append(
                    f"{name}: Giá trị {value} ngoài phạm vi thường dùng {typical}"
                )
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "adjusted_values": adjusted
        }
    
    def calculate_design(
        self,
        template_id: str,
        input_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Tính toán thiết kế dựa trên template formulas
        
        Args:
            template_id: ID của template
            input_values: Giá trị đầu vào
            
        Returns:
            Dict kết quả tính toán
        """
        template = self.get_template(template_id)
        if not template:
            return {"error": f"Template không tồn tại: {template_id}"}
        
        # Validate và lấy giá trị điều chỉnh
        validation = self.validate_input(template_id, input_values)
        values = validation["adjusted_values"]
        
        # Lấy formulas
        formulas = template.get("formulas", {})
        results = {}
        
        # Tính toán theo thứ tự formulas (có dependency)
        for name, formula_config in formulas.items():
            formula = formula_config.get("formula", "")
            description = formula_config.get("description", "")
            
            try:
                # Thay thế biến trong formula
                # Lưu ý: Đây là cách đơn giản, trong production cần parser an toàn hơn
                result = self._evaluate_formula(formula, {**values, **results})
                results[name] = {
                    "value": result,
                    "description": description
                }
            except Exception as e:
                results[name] = {
                    "value": None,
                    "error": str(e),
                    "description": description
                }
        
        return {
            "input": values,
            "validation": validation,
            "results": results,
            "template": {
                "id": template_id,
                "name": template.get("name"),
                "standards": template.get("design_standards", [])
            }
        }
    
    def _evaluate_formula(
        self,
        formula: str,
        variables: Dict[str, Any]
    ) -> float:
        """
        Đánh giá formula với các biến
        
        CẢNH BÁO: Trong production, cần dùng parser an toàn hơn eval()
        """
        import math
        
        # Chuẩn bị namespace an toàn
        safe_dict = {
            "sqrt": math.sqrt,
            "pow": pow,
            "abs": abs,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "pi": math.pi,
            "e": math.e,
        }
        
        # Thêm biến
        for key, val in variables.items():
            if isinstance(val, dict) and "value" in val:
                safe_dict[key] = val["value"]
            elif isinstance(val, (int, float)):
                safe_dict[key] = val
        
        # Chuẩn hóa formula
        formula_eval = formula.replace("²", "**2")
        formula_eval = formula_eval.replace("³", "**3")
        formula_eval = formula_eval.replace("^", "**")
        
        # Thay thế biến có tên dài (có dấu _)
        for key in sorted(variables.keys(), key=len, reverse=True):
            if key in formula_eval:
                val = variables[key]
                if isinstance(val, dict) and "value" in val:
                    val = val["value"]
                if val is not None:
                    formula_eval = formula_eval.replace(key, str(val))
        
        try:
            result = eval(formula_eval, {"__builtins__": {}}, safe_dict)
            return round(result, 4) if isinstance(result, float) else result
        except Exception:
            raise ValueError(f"Không thể tính: {formula}")
    
    def get_components(self, template_id: str) -> Optional[Dict]:
        """Lấy danh sách components của template"""
        template = self.get_template(template_id)
        if template:
            return template.get("components", {})
        return None
    
    def get_materials(self, template_id: str) -> Optional[Dict]:
        """Lấy danh sách vật liệu của template"""
        template = self.get_template(template_id)
        if template:
            return template.get("materials", {})
        return None
    
    def get_expected_efficiency(self, template_id: str) -> Optional[Dict]:
        """Lấy hiệu suất dự kiến của template"""
        template = self.get_template(template_id)
        if template:
            return template.get("expected_efficiency", {})
        return None
