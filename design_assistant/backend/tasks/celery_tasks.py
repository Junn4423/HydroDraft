"""
Celery Tasks - Các tác vụ chạy nền

Bao gồm:
- Tác vụ tính toán nặng
- Tạo bản vẽ CAD
- Xuất báo cáo
"""

from celery import Celery
from typing import Dict, Any
import os

# Cấu hình Celery
celery_app = Celery(
    "design_assistant",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 giờ timeout
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, name="tasks.design_tank")
def design_tank_task(self, design_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tác vụ thiết kế bể chạy nền
    
    Args:
        design_params: Thông số thiết kế
        
    Returns:
        Dict kết quả thiết kế
    """
    from calculations.tank_design import TankDesignCalculator
    from calculations.structural import StructuralCalculator
    from generators.dxf_generator import DXFGenerator
    
    self.update_state(state="PROGRESS", meta={"step": "Đang tính toán thủy lực..."})
    
    try:
        # 1. Tính toán thủy lực
        tank_calc = TankDesignCalculator()
        
        if design_params.get("tank_type") == "sedimentation":
            calc_result = tank_calc.design_sedimentation_tank(
                flow_rate=design_params["flow_rate"],
                detention_time=design_params.get("detention_time", 2.0),
                surface_loading_rate=design_params.get("surface_loading_rate", 35),
                depth=design_params.get("depth", 3.0),
                number_of_tanks=design_params.get("number_of_tanks", 2)
            )
        else:
            calc_result = tank_calc.design_storage_tank(
                volume=design_params["volume"],
                depth=design_params.get("depth", 3.0)
            )
        
        self.update_state(state="PROGRESS", meta={"step": "Đang tính toán kết cấu..."})
        
        # 2. Tính toán kết cấu
        struct_calc = StructuralCalculator()
        
        wall_design = struct_calc.calculate_wall_pressure(
            water_depth=calc_result["dimensions"]["depth"]
        )
        
        quantities = struct_calc.estimate_quantities(
            length=calc_result["dimensions"]["length"],
            width=calc_result["dimensions"]["width"],
            depth=calc_result["dimensions"]["depth"] + 0.3,  # + freeboard
            wall_thickness=0.25,
            bottom_thickness=0.3
        )
        
        self.update_state(state="PROGRESS", meta={"step": "Đang tạo bản vẽ..."})
        
        # 3. Tạo bản vẽ
        job_id = self.request.id[:8]
        dxf_gen = DXFGenerator(output_dir=f"./outputs/{job_id}")
        
        dxf_gen.draw_tank_plan(
            length=calc_result["dimensions"]["length"],
            width=calc_result["dimensions"]["width"],
            wall_thickness=0.25
        )
        
        dxf_gen.draw_tank_section(
            length=calc_result["dimensions"]["length"],
            total_depth=calc_result["dimensions"]["depth"] + 0.3,
            water_depth=calc_result["dimensions"]["depth"],
            wall_thickness=0.25,
            bottom_thickness=0.3,
            freeboard=0.3,
            origin=(0, -10)
        )
        
        drawing_file = dxf_gen.save(f"tank_{design_params.get('tank_name', 'design')}")
        
        return {
            "status": "completed",
            "job_id": job_id,
            "calculation": calc_result,
            "structural": {
                "wall_pressure": wall_design,
                "quantities": quantities
            },
            "drawing_file": drawing_file
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(bind=True, name="tasks.design_pipeline")
def design_pipeline_task(self, design_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tác vụ thiết kế tuyến ống chạy nền
    
    Args:
        design_params: Thông số thiết kế
        
    Returns:
        Dict kết quả thiết kế
    """
    from calculations.pipe_design import PipeDesignCalculator
    from generators.dxf_generator import DXFGenerator
    from rules.pipe_rules import PipeRules
    
    self.update_state(state="PROGRESS", meta={"step": "Đang thiết kế trắc dọc..."})
    
    try:
        pipe_calc = PipeDesignCalculator()
        pipe_rules = PipeRules()
        
        # Lấy hệ số nhám
        material = design_params.get("material", "BTCT")
        roughness = pipe_rules.get_manning_roughness(material)
        
        # Thiết kế
        if design_params.get("pipe_type") == "gravity":
            result = pipe_calc.design_gravity_pipe(
                flow_rate=design_params["design_flow"],
                profile_data=design_params["manholes"],
                pipe_diameter=design_params.get("diameter", 300),
                roughness=roughness,
                min_cover=design_params.get("min_cover_depth", 0.7)
            )
        else:
            result = pipe_calc.design_pressure_pipe(
                flow_rate=design_params["design_flow"],
                profile_data=design_params["manholes"],
                pipe_diameter=design_params.get("diameter", 200),
                roughness=roughness
            )
        
        self.update_state(state="PROGRESS", meta={"step": "Đang tạo bản vẽ..."})
        
        # Tạo bản vẽ
        job_id = self.request.id[:8]
        dxf_gen = DXFGenerator(output_dir=f"./outputs/{job_id}")
        
        dxf_gen.draw_pipe_profile(
            profile_data=result.get("manholes", []),
            pipe_segments=result.get("segments", []),
            horizontal_scale=500,
            vertical_scale=100
        )
        
        drawing_file = dxf_gen.save(f"pipeline_{design_params.get('pipeline_name', 'design')}")
        
        return {
            "status": "completed",
            "job_id": job_id,
            "design_result": result,
            "drawing_file": drawing_file
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(bind=True, name="tasks.generate_3d_model")
def generate_3d_model_task(self, design_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tác vụ tạo mô hình 3D
    
    Args:
        design_data: Dữ liệu thiết kế
        
    Returns:
        Dict với đường dẫn file 3D
    """
    from generators.cad_3d_generator import CAD3DGenerator
    
    self.update_state(state="PROGRESS", meta={"step": "Đang tạo mô hình 3D..."})
    
    try:
        job_id = self.request.id[:8]
        gen_3d = CAD3DGenerator(output_dir=f"./outputs/{job_id}")
        
        element_type = design_data.get("type")
        
        if element_type == "tank":
            gen_3d.create_tank_3d(
                length=design_data["length"],
                width=design_data["width"],
                total_depth=design_data["total_depth"],
                wall_thickness=design_data.get("wall_thickness", 0.25),
                bottom_thickness=design_data.get("bottom_thickness", 0.3)
            )
        elif element_type == "pipe_network":
            gen_3d.create_pipe_network_3d(
                segments=design_data.get("segments", []),
                manholes=design_data.get("manholes", [])
            )
        
        step_file = gen_3d.export_step(f"model_3d_{element_type}")
        
        return {
            "status": "completed",
            "job_id": job_id,
            "step_file": step_file
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(bind=True, name="tasks.generate_ifc")
def generate_ifc_task(self, design_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tác vụ tạo mô hình IFC
    
    Args:
        design_data: Dữ liệu thiết kế
        
    Returns:
        Dict với đường dẫn file IFC
    """
    from generators.ifc_generator import IFCGenerator
    
    self.update_state(state="PROGRESS", meta={"step": "Đang tạo mô hình IFC..."})
    
    try:
        job_id = self.request.id[:8]
        ifc_gen = IFCGenerator(output_dir=f"./outputs/{job_id}")
        
        ifc_gen.create_new_model(
            project_name=design_data.get("project_name", "Dự án"),
            site_name=design_data.get("site_name", "Công trường")
        )
        
        # Thêm các elements
        for element in design_data.get("elements", []):
            if element["type"] == "tank":
                ifc_gen.add_tank(
                    name=element["name"],
                    length=element["length"],
                    width=element["width"],
                    depth=element["depth"],
                    wall_thickness=element.get("wall_thickness", 0.25)
                )
            elif element["type"] == "pipe":
                ifc_gen.add_pipe_segment(
                    name=element["name"],
                    start_point=tuple(element["start_point"]),
                    end_point=tuple(element["end_point"]),
                    diameter=element["diameter"]
                )
            elif element["type"] == "manhole":
                ifc_gen.add_manhole(
                    name=element["name"],
                    x=element["x"],
                    y=element["y"],
                    ground_level=element["ground_level"],
                    invert_level=element["invert_level"]
                )
        
        ifc_file = ifc_gen.save(f"model_{design_data.get('project_name', 'project')}")
        
        return {
            "status": "completed",
            "job_id": job_id,
            "ifc_file": ifc_file
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(bind=True, name="tasks.generate_report")
def generate_report_task(self, report_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tác vụ tạo báo cáo
    
    Args:
        report_params: Thông số báo cáo
        
    Returns:
        Dict với đường dẫn file báo cáo
    """
    self.update_state(state="PROGRESS", meta={"step": "Đang tạo báo cáo..."})
    
    try:
        job_id = self.request.id[:8]
        
        # TODO: Implement report generation
        # Sử dụng Jinja2 templates + WeasyPrint cho PDF
        # hoặc python-docx cho Word
        
        return {
            "status": "completed",
            "job_id": job_id,
            "report_file": None,
            "message": "Chức năng tạo báo cáo đang được phát triển"
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
