"""
Rule Engine - Động cơ quy tắc thiết kế

Quản lý và thực thi các quy tắc thiết kế từ định nghĩa JSON và Python
"""

import json
import os
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class RuleStatus(str, Enum):
    """Trạng thái kiểm tra quy tắc"""
    PASS = "pass"           # Đạt
    WARNING = "warning"     # Cảnh báo
    FAIL = "fail"           # Không đạt
    SKIP = "skip"           # Bỏ qua

@dataclass
class RuleResult:
    """Kết quả kiểm tra quy tắc"""
    rule_id: str
    rule_name: str
    parameter: str
    value: Any
    status: RuleStatus
    message: str
    suggestion: Optional[str] = None
    standard: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "parameter": self.parameter,
            "value": self.value,
            "status": self.status.value,
            "message": self.message,
            "suggestion": self.suggestion,
            "standard": self.standard
        }

class RuleEngine:
    """
    Động cơ quy tắc thiết kế
    
    Hỗ trợ:
    - Load quy tắc từ file JSON
    - Đăng ký quy tắc Python
    - Thực thi và đánh giá quy tắc
    - Tự động điều chỉnh thông số
    """
    
    def __init__(self, rules_dir: str = None):
        self.rules: Dict[str, Dict] = {}
        self.python_rules: Dict[str, Callable] = {}
        self.rules_dir = rules_dir or os.path.join(os.path.dirname(__file__), "definitions")
        
        # Load tất cả quy tắc
        self._load_json_rules()
    
    def _load_json_rules(self):
        """Load quy tắc từ các file JSON"""
        rules_path = Path(self.rules_dir)
        if not rules_path.exists():
            rules_path.mkdir(parents=True, exist_ok=True)
            return
            
        for json_file in rules_path.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                    category = json_file.stem
                    self.rules[category] = rules_data
                    print(f"Loaded rule category: {category}")
            except Exception as e:
                print(f"Error loading rule {json_file}: {e}")
    
    def register_rule(self, rule_id: str, rule_func: Callable):
        """Đăng ký quy tắc Python"""
        self.python_rules[rule_id] = rule_func
    
    def get_rule(self, category: str, rule_id: str) -> Optional[Dict]:
        """Lấy định nghĩa quy tắc"""
        if category in self.rules:
            rules_list = self.rules[category].get("rules", [])
            for rule in rules_list:
                if rule.get("id") == rule_id:
                    return rule
        return None
    
    def validate_parameter(
        self,
        category: str,
        rule_id: str,
        value: Any,
        context: Dict = None
    ) -> RuleResult:
        """
        Kiểm tra một thông số theo quy tắc
        
        Args:
            category: Danh mục quy tắc (tank, pipe, structural)
            rule_id: ID quy tắc
            value: Giá trị cần kiểm tra
            context: Ngữ cảnh bổ sung
            
        Returns:
            RuleResult: Kết quả kiểm tra
        """
        rule = self.get_rule(category, rule_id)
        if not rule:
            return RuleResult(
                rule_id=rule_id,
                rule_name="Không xác định",
                parameter=rule_id,
                value=value,
                status=RuleStatus.SKIP,
                message=f"Không tìm thấy quy tắc: {rule_id}"
            )
        
        # Lấy các giới hạn
        min_val = rule.get("min")
        max_val = rule.get("max")
        recommended_min = rule.get("recommended_min", min_val)
        recommended_max = rule.get("recommended_max", max_val)
        
        # Đánh giá context nếu có
        if context:
            min_val = self._evaluate_expression(min_val, context)
            max_val = self._evaluate_expression(max_val, context)
            recommended_min = self._evaluate_expression(recommended_min, context)
            recommended_max = self._evaluate_expression(recommended_max, context)
        
        # Kiểm tra
        status = RuleStatus.PASS
        message = rule.get("pass_message", "Đạt yêu cầu")
        suggestion = None
        
        if min_val is not None and value < min_val:
            status = RuleStatus.FAIL
            message = rule.get("fail_message", f"Giá trị {value} nhỏ hơn giới hạn tối thiểu {min_val}")
            suggestion = f"Tăng giá trị lên ít nhất {min_val}"
        elif max_val is not None and value > max_val:
            status = RuleStatus.FAIL
            message = rule.get("fail_message", f"Giá trị {value} lớn hơn giới hạn tối đa {max_val}")
            suggestion = f"Giảm giá trị xuống tối đa {max_val}"
        elif recommended_min is not None and value < recommended_min:
            status = RuleStatus.WARNING
            message = rule.get("warning_message", f"Giá trị {value} thấp hơn khuyến nghị {recommended_min}")
            suggestion = f"Khuyến nghị tăng lên {recommended_min}"
        elif recommended_max is not None and value > recommended_max:
            status = RuleStatus.WARNING
            message = rule.get("warning_message", f"Giá trị {value} cao hơn khuyến nghị {recommended_max}")
            suggestion = f"Khuyến nghị giảm xuống {recommended_max}"
        
        return RuleResult(
            rule_id=rule_id,
            rule_name=rule.get("name", rule_id),
            parameter=rule.get("parameter", rule_id),
            value=value,
            status=status,
            message=message,
            suggestion=suggestion,
            standard=rule.get("standard")
        )
    
    def validate_all(
        self,
        category: str,
        parameters: Dict[str, Any],
        context: Dict = None
    ) -> List[RuleResult]:
        """
        Kiểm tra tất cả thông số theo một danh mục quy tắc
        
        Args:
            category: Danh mục quy tắc
            parameters: Dict các thông số cần kiểm tra
            context: Ngữ cảnh bổ sung
            
        Returns:
            List[RuleResult]: Danh sách kết quả kiểm tra
        """
        results = []
        
        if category not in self.rules:
            return results
        
        rules_list = self.rules[category].get("rules", [])
        
        for rule in rules_list:
            param_name = rule.get("parameter")
            if param_name in parameters:
                result = self.validate_parameter(
                    category=category,
                    rule_id=rule["id"],
                    value=parameters[param_name],
                    context=context
                )
                results.append(result)
        
        return results
    
    def auto_adjust(
        self,
        category: str,
        parameters: Dict[str, Any],
        context: Dict = None
    ) -> Dict[str, Any]:
        """
        Tự động điều chỉnh thông số theo quy tắc
        
        Args:
            category: Danh mục quy tắc
            parameters: Dict các thông số
            context: Ngữ cảnh bổ sung
            
        Returns:
            Dict: Thông số đã điều chỉnh
        """
        adjusted = parameters.copy()
        
        if category not in self.rules:
            return adjusted
        
        rules_list = self.rules[category].get("rules", [])
        
        for rule in rules_list:
            param_name = rule.get("parameter")
            if param_name not in adjusted:
                continue
            
            value = adjusted[param_name]
            min_val = rule.get("min")
            max_val = rule.get("max")
            
            # Đánh giá context
            if context:
                min_val = self._evaluate_expression(min_val, context)
                max_val = self._evaluate_expression(max_val, context)
            
            # Điều chỉnh
            if min_val is not None and value < min_val:
                adjusted[param_name] = min_val
            elif max_val is not None and value > max_val:
                adjusted[param_name] = max_val
        
        return adjusted
    
    def _evaluate_expression(self, expr: Any, context: Dict) -> Any:
        """Đánh giá biểu thức với context"""
        if expr is None:
            return None
        if isinstance(expr, (int, float)):
            return expr
        if isinstance(expr, str):
            try:
                # Thay thế các biến từ context
                for key, value in context.items():
                    expr = expr.replace(f"${{{key}}}", str(value))
                # Đánh giá biểu thức an toàn
                return eval(expr, {"__builtins__": {}}, context)
            except:
                return expr
        return expr
    
    def get_recommendations(
        self,
        category: str,
        design_type: str = None
    ) -> Dict[str, Any]:
        """
        Lấy các giá trị khuyến nghị cho một loại thiết kế
        
        Args:
            category: Danh mục quy tắc
            design_type: Loại thiết kế cụ thể
            
        Returns:
            Dict: Các giá trị khuyến nghị
        """
        recommendations = {}
        
        if category not in self.rules:
            return recommendations
        
        rules_list = self.rules[category].get("rules", [])
        
        for rule in rules_list:
            param_name = rule.get("parameter")
            
            # Lấy giá trị khuyến nghị
            if design_type and "type_specific" in rule:
                type_rules = rule["type_specific"].get(design_type, {})
                recommended = type_rules.get("recommended", rule.get("recommended"))
            else:
                recommended = rule.get("recommended")
            
            if recommended is not None:
                recommendations[param_name] = recommended
        
        return recommendations


# Singleton instance
_rule_engine = None

def get_rule_engine() -> RuleEngine:
    """Lấy instance của RuleEngine (singleton)"""
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine()
    return _rule_engine
