"""
Version Management System - Sprint 4: Engineering Version Control

Quản lý phiên bản thiết kế:
- So sánh versions
- Diff reports
- History viewer
- Rollback support
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import os
import uuid
import hashlib
import difflib


class ChangeType(str, Enum):
    """Loại thay đổi"""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class VersionStatus(str, Enum):
    """Trạng thái version"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


@dataclass
class ParameterChange:
    """Thay đổi của một parameter"""
    parameter_name: str
    change_type: ChangeType
    old_value: Any = None
    new_value: Any = None
    unit: str = ""
    
    @property
    def percent_change(self) -> Optional[float]:
        """Tính % thay đổi cho giá trị số"""
        if self.change_type == ChangeType.MODIFIED:
            if isinstance(self.old_value, (int, float)) and isinstance(self.new_value, (int, float)):
                if self.old_value != 0:
                    return ((self.new_value - self.old_value) / self.old_value) * 100
        return None
    
    def to_dict(self) -> Dict:
        return {
            "parameter": self.parameter_name,
            "change_type": self.change_type.value,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "unit": self.unit,
            "percent_change": self.percent_change
        }


@dataclass
class ElementChange:
    """Thay đổi của một element"""
    element_id: str
    element_name: str
    element_type: str
    change_type: ChangeType
    parameter_changes: List[ParameterChange] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "element_id": self.element_id,
            "element_name": self.element_name,
            "element_type": self.element_type,
            "change_type": self.change_type.value,
            "parameter_changes": [p.to_dict() for p in self.parameter_changes],
            "total_changes": len(self.parameter_changes)
        }


@dataclass
class VersionDiff:
    """Báo cáo so sánh 2 versions"""
    version_from: str
    version_to: str
    created_at: datetime = field(default_factory=datetime.now)
    
    # Summary
    elements_added: int = 0
    elements_removed: int = 0
    elements_modified: int = 0
    
    # Detailed changes
    changes: List[ElementChange] = field(default_factory=list)
    
    # Calculation changes
    calculation_diff: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "version_from": self.version_from,
            "version_to": self.version_to,
            "created_at": self.created_at.isoformat(),
            "summary": {
                "elements_added": self.elements_added,
                "elements_removed": self.elements_removed,
                "elements_modified": self.elements_modified,
                "total_changes": self.elements_added + self.elements_removed + self.elements_modified
            },
            "changes": [c.to_dict() for c in self.changes],
            "calculation_diff": self.calculation_diff
        }


@dataclass
class DesignSnapshot:
    """Snapshot của một version"""
    version_id: str
    version_number: int
    version_tag: str
    project_id: str
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    description: str = ""
    status: VersionStatus = VersionStatus.DRAFT
    
    # Input data
    input_params: Dict[str, Any] = field(default_factory=dict)
    
    # Calculation results
    calculation_log: Dict[str, Any] = field(default_factory=dict)
    
    # Output files
    output_files: List[Dict[str, str]] = field(default_factory=list)
    
    # Ruleset
    applied_rules: Dict[str, Any] = field(default_factory=dict)
    
    # Overrides
    has_overrides: bool = False
    override_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # Hash for integrity
    content_hash: str = ""
    
    def calculate_hash(self) -> str:
        """Tính hash của nội dung"""
        content = json.dumps({
            "input_params": self.input_params,
            "calculation_log": self.calculation_log,
            "applied_rules": self.applied_rules
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict:
        return {
            "version_id": self.version_id,
            "version_number": self.version_number,
            "version_tag": self.version_tag,
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "description": self.description,
            "status": self.status.value,
            "input_params": self.input_params,
            "calculation_log": self.calculation_log,
            "output_files": self.output_files,
            "applied_rules": self.applied_rules,
            "has_overrides": self.has_overrides,
            "override_log": self.override_log,
            "content_hash": self.content_hash
        }


class VersionManager:
    """
    Quản lý versions của thiết kế
    
    Features:
    - Create/save versions
    - Compare versions
    - Generate diff reports
    - Rollback support
    - Audit trail
    """
    
    def __init__(self, storage_path: str = "./data/versions"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
        # In-memory cache
        self._versions: Dict[str, DesignSnapshot] = {}
        self._project_versions: Dict[str, List[str]] = {}  # project_id -> version_ids
    
    def create_version(
        self,
        project_id: str,
        input_params: Dict[str, Any],
        calculation_log: Dict[str, Any],
        output_files: List[Dict[str, str]] = None,
        applied_rules: Dict[str, Any] = None,
        override_log: List[Dict[str, Any]] = None,
        description: str = "",
        created_by: str = "system",
        tag: str = None
    ) -> DesignSnapshot:
        """
        Tạo version mới
        
        Args:
            project_id: ID dự án
            input_params: Thông số đầu vào
            calculation_log: Kết quả tính toán
            output_files: Danh sách file output
            applied_rules: Rules đã áp dụng
            override_log: Log các override
            description: Mô tả version
            created_by: Người tạo
            tag: Tag version (v1.0, draft, final, etc.)
            
        Returns:
            DesignSnapshot: Version đã tạo
        """
        # Determine version number
        existing = self._project_versions.get(project_id, [])
        version_number = len(existing) + 1
        
        # Generate version ID
        version_id = f"VER_{uuid.uuid4().hex[:12].upper()}"
        
        # Auto-generate tag if not provided
        if not tag:
            tag = f"v{version_number}.0"
        
        # Create snapshot
        snapshot = DesignSnapshot(
            version_id=version_id,
            version_number=version_number,
            version_tag=tag,
            project_id=project_id,
            created_by=created_by,
            description=description,
            input_params=input_params,
            calculation_log=calculation_log,
            output_files=output_files or [],
            applied_rules=applied_rules or {},
            has_overrides=bool(override_log),
            override_log=override_log or []
        )
        
        # Calculate hash
        snapshot.content_hash = snapshot.calculate_hash()
        
        # Store
        self._versions[version_id] = snapshot
        
        if project_id not in self._project_versions:
            self._project_versions[project_id] = []
        self._project_versions[project_id].append(version_id)
        
        # Save to disk
        self._save_version(snapshot)
        
        return snapshot
    
    def get_version(self, version_id: str) -> Optional[DesignSnapshot]:
        """Lấy version theo ID"""
        if version_id in self._versions:
            return self._versions[version_id]
        
        # Try load from disk
        return self._load_version(version_id)
    
    def get_project_versions(self, project_id: str) -> List[DesignSnapshot]:
        """Lấy tất cả versions của project"""
        version_ids = self._project_versions.get(project_id, [])
        versions = []
        for vid in version_ids:
            v = self.get_version(vid)
            if v:
                versions.append(v)
        return sorted(versions, key=lambda x: x.version_number)
    
    def get_latest_version(self, project_id: str) -> Optional[DesignSnapshot]:
        """Lấy version mới nhất"""
        versions = self.get_project_versions(project_id)
        return versions[-1] if versions else None
    
    def compare_versions(
        self,
        version_id_from: str,
        version_id_to: str
    ) -> VersionDiff:
        """
        So sánh 2 versions
        
        Args:
            version_id_from: Version cũ
            version_id_to: Version mới
            
        Returns:
            VersionDiff: Báo cáo so sánh
        """
        v_from = self.get_version(version_id_from)
        v_to = self.get_version(version_id_to)
        
        if not v_from or not v_to:
            raise ValueError("Version not found")
        
        diff = VersionDiff(
            version_from=version_id_from,
            version_to=version_id_to
        )
        
        # Compare input params
        diff.changes.extend(
            self._compare_params(v_from.input_params, v_to.input_params, "input")
        )
        
        # Compare calculation results
        diff.calculation_diff = self._compare_calculations(
            v_from.calculation_log,
            v_to.calculation_log
        )
        
        # Count changes
        for change in diff.changes:
            if change.change_type == ChangeType.ADDED:
                diff.elements_added += 1
            elif change.change_type == ChangeType.REMOVED:
                diff.elements_removed += 1
            elif change.change_type == ChangeType.MODIFIED:
                diff.elements_modified += 1
        
        return diff
    
    def _compare_params(
        self,
        old_params: Dict[str, Any],
        new_params: Dict[str, Any],
        element_type: str
    ) -> List[ElementChange]:
        """So sánh parameters"""
        changes = []
        
        all_keys = set(old_params.keys()) | set(new_params.keys())
        
        for key in all_keys:
            old_val = old_params.get(key)
            new_val = new_params.get(key)
            
            if key not in old_params:
                # Added
                changes.append(ElementChange(
                    element_id=key,
                    element_name=key,
                    element_type=element_type,
                    change_type=ChangeType.ADDED,
                    parameter_changes=[ParameterChange(
                        parameter_name=key,
                        change_type=ChangeType.ADDED,
                        new_value=new_val
                    )]
                ))
            elif key not in new_params:
                # Removed
                changes.append(ElementChange(
                    element_id=key,
                    element_name=key,
                    element_type=element_type,
                    change_type=ChangeType.REMOVED,
                    parameter_changes=[ParameterChange(
                        parameter_name=key,
                        change_type=ChangeType.REMOVED,
                        old_value=old_val
                    )]
                ))
            elif old_val != new_val:
                # Modified
                if isinstance(old_val, dict) and isinstance(new_val, dict):
                    # Nested comparison
                    nested_changes = self._compare_nested_dict(old_val, new_val)
                    if nested_changes:
                        changes.append(ElementChange(
                            element_id=key,
                            element_name=key,
                            element_type=element_type,
                            change_type=ChangeType.MODIFIED,
                            parameter_changes=nested_changes
                        ))
                else:
                    changes.append(ElementChange(
                        element_id=key,
                        element_name=key,
                        element_type=element_type,
                        change_type=ChangeType.MODIFIED,
                        parameter_changes=[ParameterChange(
                            parameter_name=key,
                            change_type=ChangeType.MODIFIED,
                            old_value=old_val,
                            new_value=new_val
                        )]
                    ))
        
        return changes
    
    def _compare_nested_dict(
        self,
        old_dict: Dict,
        new_dict: Dict
    ) -> List[ParameterChange]:
        """So sánh nested dictionary"""
        changes = []
        all_keys = set(old_dict.keys()) | set(new_dict.keys())
        
        for key in all_keys:
            old_val = old_dict.get(key)
            new_val = new_dict.get(key)
            
            if key not in old_dict:
                changes.append(ParameterChange(
                    parameter_name=key,
                    change_type=ChangeType.ADDED,
                    new_value=new_val
                ))
            elif key not in new_dict:
                changes.append(ParameterChange(
                    parameter_name=key,
                    change_type=ChangeType.REMOVED,
                    old_value=old_val
                ))
            elif old_val != new_val:
                changes.append(ParameterChange(
                    parameter_name=key,
                    change_type=ChangeType.MODIFIED,
                    old_value=old_val,
                    new_value=new_val
                ))
        
        return changes
    
    def _compare_calculations(
        self,
        old_calc: Dict,
        new_calc: Dict
    ) -> Dict[str, Any]:
        """So sánh kết quả tính toán"""
        diff = {
            "changed_steps": [],
            "added_steps": [],
            "removed_steps": []
        }
        
        old_steps = old_calc.get("steps", [])
        new_steps = new_calc.get("steps", [])
        
        old_step_ids = {s.get("step_id"): s for s in old_steps if isinstance(s, dict)}
        new_step_ids = {s.get("step_id"): s for s in new_steps if isinstance(s, dict)}
        
        # Find added
        for sid in new_step_ids:
            if sid not in old_step_ids:
                diff["added_steps"].append(sid)
        
        # Find removed
        for sid in old_step_ids:
            if sid not in new_step_ids:
                diff["removed_steps"].append(sid)
        
        # Find changed
        for sid in old_step_ids:
            if sid in new_step_ids:
                old_result = old_step_ids[sid].get("result")
                new_result = new_step_ids[sid].get("result")
                if old_result != new_result:
                    diff["changed_steps"].append({
                        "step_id": sid,
                        "old_result": old_result,
                        "new_result": new_result
                    })
        
        return diff
    
    def generate_diff_report(
        self,
        version_id_from: str,
        version_id_to: str,
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Tạo báo cáo diff
        
        Args:
            version_id_from: Version cũ
            version_id_to: Version mới
            output_format: "json", "html", "text"
            
        Returns:
            Dict với báo cáo
        """
        diff = self.compare_versions(version_id_from, version_id_to)
        v_from = self.get_version(version_id_from)
        v_to = self.get_version(version_id_to)
        
        report = {
            "title": f"Version Comparison Report",
            "generated_at": datetime.now().isoformat(),
            "from_version": {
                "id": version_id_from,
                "tag": v_from.version_tag if v_from else "",
                "created_at": v_from.created_at.isoformat() if v_from else ""
            },
            "to_version": {
                "id": version_id_to,
                "tag": v_to.version_tag if v_to else "",
                "created_at": v_to.created_at.isoformat() if v_to else ""
            },
            "summary": {
                "total_changes": diff.elements_added + diff.elements_removed + diff.elements_modified,
                "added": diff.elements_added,
                "removed": diff.elements_removed,
                "modified": diff.elements_modified
            },
            "details": diff.to_dict()
        }
        
        return report
    
    def get_version_history(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Lấy lịch sử versions của project
        
        Returns:
            List of version summaries
        """
        versions = self.get_project_versions(project_id)
        
        history = []
        for v in versions:
            history.append({
                "version_id": v.version_id,
                "version_number": v.version_number,
                "version_tag": v.version_tag,
                "status": v.status.value,
                "created_at": v.created_at.isoformat(),
                "created_by": v.created_by,
                "description": v.description,
                "has_overrides": v.has_overrides,
                "content_hash": v.content_hash
            })
        
        return history
    
    def update_version_status(
        self,
        version_id: str,
        status: VersionStatus,
        updated_by: str = "system"
    ) -> bool:
        """Cập nhật trạng thái version"""
        version = self.get_version(version_id)
        if not version:
            return False
        
        version.status = status
        self._save_version(version)
        return True
    
    def approve_version(
        self,
        version_id: str,
        approved_by: str,
        notes: str = ""
    ) -> bool:
        """Phê duyệt version"""
        return self.update_version_status(
            version_id,
            VersionStatus.APPROVED,
            approved_by
        )
    
    def _save_version(self, snapshot: DesignSnapshot) -> str:
        """Lưu version ra file"""
        project_dir = os.path.join(self.storage_path, snapshot.project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        filepath = os.path.join(project_dir, f"{snapshot.version_id}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(snapshot.to_dict(), f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _load_version(self, version_id: str) -> Optional[DesignSnapshot]:
        """Load version từ file"""
        # Search in all project directories
        for project_id in os.listdir(self.storage_path):
            project_dir = os.path.join(self.storage_path, project_id)
            if os.path.isdir(project_dir):
                filepath = os.path.join(project_dir, f"{version_id}.json")
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    snapshot = DesignSnapshot(
                        version_id=data["version_id"],
                        version_number=data["version_number"],
                        version_tag=data["version_tag"],
                        project_id=data["project_id"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        created_by=data["created_by"],
                        description=data["description"],
                        status=VersionStatus(data["status"]),
                        input_params=data["input_params"],
                        calculation_log=data["calculation_log"],
                        output_files=data["output_files"],
                        applied_rules=data["applied_rules"],
                        has_overrides=data["has_overrides"],
                        override_log=data["override_log"],
                        content_hash=data["content_hash"]
                    )
                    
                    # Cache
                    self._versions[version_id] = snapshot
                    
                    return snapshot
        
        return None
    
    def rollback_to_version(
        self,
        project_id: str,
        version_id: str,
        created_by: str = "system"
    ) -> DesignSnapshot:
        """
        Rollback về version cũ
        
        Tạo một version mới với nội dung của version cũ
        """
        old_version = self.get_version(version_id)
        if not old_version:
            raise ValueError(f"Version {version_id} not found")
        
        # Create new version from old data
        new_version = self.create_version(
            project_id=project_id,
            input_params=old_version.input_params,
            calculation_log=old_version.calculation_log,
            output_files=old_version.output_files,
            applied_rules=old_version.applied_rules,
            override_log=old_version.override_log,
            description=f"Rollback from {old_version.version_tag}",
            created_by=created_by,
            tag=f"rollback-{old_version.version_tag}"
        )
        
        return new_version


# Singleton instance
_version_manager: Optional[VersionManager] = None

def get_version_manager(storage_path: str = None) -> VersionManager:
    """Get or create VersionManager instance"""
    global _version_manager
    if _version_manager is None:
        _version_manager = VersionManager(storage_path or "./data/versions")
    return _version_manager
