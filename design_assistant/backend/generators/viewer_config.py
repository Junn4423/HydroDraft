"""
3D Viewer Configuration - Sprint 4: BIM & Enterprise

Cấu hình cho IFC.js / web-ifc-viewer integration
Metadata viewer và section tools
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import os


class ViewerMode(str, Enum):
    """Chế độ xem"""
    ORBIT = "orbit"
    PAN = "pan"
    ZOOM = "zoom"
    SECTION = "section"
    MEASURE = "measure"


class SectionPlane(str, Enum):
    """Mặt cắt"""
    XY = "xy"  # Plan view
    XZ = "xz"  # Front elevation
    YZ = "yz"  # Side elevation
    FREE = "free"  # Custom plane


@dataclass
class ViewerSettings:
    """Cài đặt viewer"""
    background_color: Tuple[int, int, int] = (240, 240, 240)
    ambient_light_intensity: float = 0.5
    directional_light_intensity: float = 0.8
    show_grid: bool = True
    grid_size: float = 100.0
    grid_divisions: int = 100
    show_axes: bool = True
    selection_color: Tuple[int, int, int] = (255, 165, 0)
    highlight_color: Tuple[int, int, int] = (65, 105, 225)
    
    def to_dict(self) -> Dict:
        return {
            "background": f"rgb({self.background_color[0]},{self.background_color[1]},{self.background_color[2]})",
            "lighting": {
                "ambient": self.ambient_light_intensity,
                "directional": self.directional_light_intensity
            },
            "grid": {
                "visible": self.show_grid,
                "size": self.grid_size,
                "divisions": self.grid_divisions
            },
            "axes": {"visible": self.show_axes},
            "selection": {
                "color": f"rgb({self.selection_color[0]},{self.selection_color[1]},{self.selection_color[2]})"
            },
            "highlight": {
                "color": f"rgb({self.highlight_color[0]},{self.highlight_color[1]},{self.highlight_color[2]})"
            }
        }


@dataclass
class CameraPosition:
    """Vị trí camera"""
    eye: Tuple[float, float, float] = (50, 50, 50)
    target: Tuple[float, float, float] = (0, 0, 0)
    up: Tuple[float, float, float] = (0, 0, 1)
    fov: float = 45.0
    near: float = 0.1
    far: float = 1000.0
    
    def to_dict(self) -> Dict:
        return {
            "eye": {"x": self.eye[0], "y": self.eye[1], "z": self.eye[2]},
            "target": {"x": self.target[0], "y": self.target[1], "z": self.target[2]},
            "up": {"x": self.up[0], "y": self.up[1], "z": self.up[2]},
            "fov": self.fov,
            "near": self.near,
            "far": self.far
        }


@dataclass
class SectionConfig:
    """Cấu hình mặt cắt"""
    plane: SectionPlane = SectionPlane.XY
    position: float = 0.0
    normal: Tuple[float, float, float] = (0, 0, 1)
    enabled: bool = False
    fill_color: Tuple[int, int, int] = (200, 200, 200)
    
    def to_dict(self) -> Dict:
        return {
            "plane": self.plane.value,
            "position": self.position,
            "normal": {"x": self.normal[0], "y": self.normal[1], "z": self.normal[2]},
            "enabled": self.enabled,
            "fillColor": f"rgb({self.fill_color[0]},{self.fill_color[1]},{self.fill_color[2]})"
        }


class ViewerConfig:
    """
    Cấu hình cho 3D viewer (IFC.js/web-ifc-viewer)
    
    Tạo config JSON cho frontend integration
    """
    
    # Predefined camera views
    STANDARD_VIEWS = {
        "top": CameraPosition(eye=(0, 0, 100), target=(0, 0, 0), up=(0, 1, 0)),
        "bottom": CameraPosition(eye=(0, 0, -100), target=(0, 0, 0), up=(0, 1, 0)),
        "front": CameraPosition(eye=(0, -100, 0), target=(0, 0, 0), up=(0, 0, 1)),
        "back": CameraPosition(eye=(0, 100, 0), target=(0, 0, 0), up=(0, 0, 1)),
        "left": CameraPosition(eye=(-100, 0, 0), target=(0, 0, 0), up=(0, 0, 1)),
        "right": CameraPosition(eye=(100, 0, 0), target=(0, 0, 0), up=(0, 0, 1)),
        "isometric": CameraPosition(eye=(50, 50, 50), target=(0, 0, 0), up=(0, 0, 1)),
        "isometric_back": CameraPosition(eye=(-50, -50, 50), target=(0, 0, 0), up=(0, 0, 1))
    }
    
    def __init__(self):
        self.settings = ViewerSettings()
        self.camera = CameraPosition()
        self.sections: List[SectionConfig] = []
        self.visible_categories: List[str] = []
        self.hidden_elements: List[str] = []
    
    def set_view(self, view_name: str):
        """Set predefined view"""
        if view_name in self.STANDARD_VIEWS:
            self.camera = self.STANDARD_VIEWS[view_name]
    
    def add_section(
        self,
        plane: SectionPlane,
        position: float = 0.0,
        enabled: bool = True
    ):
        """Thêm mặt cắt"""
        normal_map = {
            SectionPlane.XY: (0, 0, 1),
            SectionPlane.XZ: (0, 1, 0),
            SectionPlane.YZ: (1, 0, 0),
            SectionPlane.FREE: (0, 0, 1)
        }
        
        section = SectionConfig(
            plane=plane,
            position=position,
            normal=normal_map[plane],
            enabled=enabled
        )
        self.sections.append(section)
    
    def to_json(self) -> str:
        """Export to JSON config"""
        config = {
            "settings": self.settings.to_dict(),
            "camera": self.camera.to_dict(),
            "sections": [s.to_dict() for s in self.sections],
            "visibility": {
                "categories": self.visible_categories,
                "hiddenElements": self.hidden_elements
            },
            "standardViews": {
                name: view.to_dict() 
                for name, view in self.STANDARD_VIEWS.items()
            }
        }
        return json.dumps(config, indent=2)


def generate_viewer_html(
    ifc_url: str,
    container_id: str = "viewer-container",
    width: str = "100%",
    height: str = "600px"
) -> str:
    """
    Tạo HTML snippet cho IFC.js viewer
    
    Args:
        ifc_url: URL to IFC file
        container_id: Container element ID
        width: Width CSS
        height: Height CSS
        
    Returns:
        HTML string
    """
    html = f'''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HydroDraft 3D Viewer</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #1a1a2e;
            color: #eee;
        }}
        #{container_id} {{
            width: {width};
            height: {height};
            position: relative;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        }}
        .viewer-toolbar {{
            position: absolute;
            top: 10px;
            left: 10px;
            z-index: 100;
            display: flex;
            gap: 5px;
        }}
        .viewer-toolbar button {{
            padding: 8px 12px;
            border: none;
            border-radius: 4px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .viewer-toolbar button:hover {{
            background: rgba(255,255,255,0.2);
        }}
        .viewer-toolbar button.active {{
            background: #4361ee;
        }}
        .metadata-panel {{
            position: absolute;
            top: 10px;
            right: 10px;
            width: 300px;
            max-height: calc(100% - 20px);
            background: rgba(0,0,0,0.8);
            border-radius: 8px;
            padding: 15px;
            overflow-y: auto;
            z-index: 100;
            display: none;
        }}
        .metadata-panel.visible {{
            display: block;
        }}
        .metadata-panel h3 {{
            margin-bottom: 10px;
            color: #4361ee;
            border-bottom: 1px solid #333;
            padding-bottom: 5px;
        }}
        .metadata-item {{
            margin: 8px 0;
            font-size: 13px;
        }}
        .metadata-item label {{
            color: #888;
            display: block;
            font-size: 11px;
        }}
        .section-controls {{
            position: absolute;
            bottom: 10px;
            left: 10px;
            z-index: 100;
            background: rgba(0,0,0,0.7);
            padding: 10px;
            border-radius: 8px;
        }}
        .section-controls label {{
            display: block;
            margin: 5px 0;
            font-size: 12px;
        }}
        .section-controls input[type="range"] {{
            width: 150px;
        }}
    </style>
</head>
<body>
    <div id="{container_id}">
        <!-- Toolbar -->
        <div class="viewer-toolbar">
            <button id="btn-orbit" class="active" title="Orbit">🔄 Orbit</button>
            <button id="btn-pan" title="Pan">✋ Pan</button>
            <button id="btn-zoom" title="Zoom">🔍 Zoom</button>
            <button id="btn-section" title="Section">✂️ Section</button>
            <button id="btn-fit" title="Fit All">📐 Fit</button>
            <button id="btn-views" title="Views">📷 Views</button>
            <button id="btn-metadata" title="Properties">📋 Props</button>
        </div>
        
        <!-- Metadata Panel -->
        <div class="metadata-panel" id="metadata-panel">
            <h3>Element Properties</h3>
            <div id="metadata-content">
                <p style="color:#888;">Click an element to see properties</p>
            </div>
        </div>
        
        <!-- Section Controls -->
        <div class="section-controls" id="section-controls" style="display:none;">
            <h4 style="margin-bottom:10px;">Section Plane</h4>
            <label>
                <input type="checkbox" id="section-enabled"> Enable Section
            </label>
            <label>
                Position: <span id="section-pos-value">0</span>m
                <input type="range" id="section-position" min="-50" max="50" value="0">
            </label>
            <label>
                Plane:
                <select id="section-plane">
                    <option value="xy">XY (Plan)</option>
                    <option value="xz">XZ (Front)</option>
                    <option value="yz">YZ (Side)</option>
                </select>
            </label>
        </div>
        
        <!-- Canvas will be inserted here by IFC.js -->
    </div>
    
    <!-- IFC.js / web-ifc-viewer -->
    <script type="module">
        import {{ IfcViewerAPI }} from 'https://cdn.jsdelivr.net/npm/web-ifc-viewer@1.0.220/dist/web-ifc-viewer.min.js';
        
        const container = document.getElementById('{container_id}');
        const viewer = new IfcViewerAPI({{
            container,
            backgroundColor: new THREE.Color(0x1a1a2e)
        }});
        
        // Setup
        viewer.grid.setGrid();
        viewer.axes.setAxes();
        
        // Load IFC
        const ifcUrl = '{ifc_url}';
        async function loadIFC() {{
            try {{
                const model = await viewer.IFC.loadIfcUrl(ifcUrl);
                viewer.shadowDropper.renderShadow(model.modelID);
                console.log('IFC loaded successfully');
            }} catch (error) {{
                console.error('Error loading IFC:', error);
            }}
        }}
        loadIFC();
        
        // Toolbar interactions
        document.getElementById('btn-orbit').onclick = () => setMode('orbit');
        document.getElementById('btn-pan').onclick = () => setMode('pan');
        document.getElementById('btn-zoom').onclick = () => setMode('zoom');
        document.getElementById('btn-fit').onclick = () => viewer.IFC.fitModelToFrame();
        document.getElementById('btn-section').onclick = toggleSection;
        document.getElementById('btn-metadata').onclick = toggleMetadata;
        
        function setMode(mode) {{
            document.querySelectorAll('.viewer-toolbar button').forEach(b => b.classList.remove('active'));
            document.getElementById('btn-' + mode)?.classList.add('active');
        }}
        
        function toggleSection() {{
            const controls = document.getElementById('section-controls');
            controls.style.display = controls.style.display === 'none' ? 'block' : 'none';
        }}
        
        function toggleMetadata() {{
            const panel = document.getElementById('metadata-panel');
            panel.classList.toggle('visible');
        }}
        
        // Section plane
        document.getElementById('section-position').oninput = (e) => {{
            document.getElementById('section-pos-value').textContent = e.target.value;
            // Update section plane position
        }};
        
        // Element selection
        container.ondblclick = async () => {{
            const result = await viewer.IFC.selector.pickIfcItem(true);
            if (result) {{
                const props = await viewer.IFC.getProperties(result.modelID, result.id, true, true);
                showMetadata(props);
            }}
        }};
        
        function showMetadata(props) {{
            const content = document.getElementById('metadata-content');
            let html = '';
            
            if (props.Name) {{
                html += `<div class="metadata-item"><label>Name</label>${{props.Name.value || 'N/A'}}</div>`;
            }}
            if (props.ObjectType) {{
                html += `<div class="metadata-item"><label>Type</label>${{props.ObjectType.value || 'N/A'}}</div>`;
            }}
            if (props.GlobalId) {{
                html += `<div class="metadata-item"><label>Global ID</label>${{props.GlobalId.value || 'N/A'}}</div>`;
            }}
            
            // Property sets
            if (props.psets) {{
                for (const pset of props.psets) {{
                    html += `<h4 style="margin-top:15px;color:#4cc9f0;">${{pset.Name?.value || 'Properties'}}</h4>`;
                    if (pset.HasProperties) {{
                        for (const prop of pset.HasProperties) {{
                            const value = prop.NominalValue?.value || 'N/A';
                            html += `<div class="metadata-item"><label>${{prop.Name?.value}}</label>${{value}}</div>`;
                        }}
                    }}
                }}
            }}
            
            content.innerHTML = html || '<p>No properties available</p>';
            document.getElementById('metadata-panel').classList.add('visible');
        }}
        
        // Keyboard shortcuts
        document.onkeydown = (e) => {{
            switch(e.key) {{
                case 'f': viewer.IFC.fitModelToFrame(); break;
                case 'Escape': viewer.IFC.selector.unPick(); break;
            }}
        }};
    </script>
</body>
</html>
'''
    return html


def generate_react_viewer_component() -> str:
    """
    Tạo React component cho IFC viewer
    
    Returns:
        React component code
    """
    component = '''
import React, { useEffect, useRef, useState } from 'react';
import { IfcViewerAPI } from 'web-ifc-viewer';
import * as THREE from 'three';

const IFCViewer = ({ 
    ifcUrl, 
    width = '100%', 
    height = '600px',
    onElementSelect,
    onLoad,
    onError 
}) => {
    const containerRef = useRef(null);
    const viewerRef = useRef(null);
    const [loading, setLoading] = useState(false);
    const [selectedElement, setSelectedElement] = useState(null);
    const [sectionEnabled, setSectionEnabled] = useState(false);
    const [sectionPosition, setSectionPosition] = useState(0);
    const [showProperties, setShowProperties] = useState(false);
    
    useEffect(() => {
        if (!containerRef.current) return;
        
        // Initialize viewer
        const viewer = new IfcViewerAPI({
            container: containerRef.current,
            backgroundColor: new THREE.Color(0x1a1a2e)
        });
        
        viewer.grid.setGrid();
        viewer.axes.setAxes();
        viewerRef.current = viewer;
        
        // Load IFC
        if (ifcUrl) {
            loadIFC(viewer, ifcUrl);
        }
        
        return () => {
            viewer.dispose();
        };
    }, []);
    
    useEffect(() => {
        if (viewerRef.current && ifcUrl) {
            loadIFC(viewerRef.current, ifcUrl);
        }
    }, [ifcUrl]);
    
    const loadIFC = async (viewer, url) => {
        setLoading(true);
        try {
            const model = await viewer.IFC.loadIfcUrl(url);
            viewer.shadowDropper.renderShadow(model.modelID);
            onLoad?.(model);
        } catch (error) {
            console.error('Error loading IFC:', error);
            onError?.(error);
        } finally {
            setLoading(false);
        }
    };
    
    const handleDoubleClick = async () => {
        const viewer = viewerRef.current;
        if (!viewer) return;
        
        const result = await viewer.IFC.selector.pickIfcItem(true);
        if (result) {
            const props = await viewer.IFC.getProperties(
                result.modelID, 
                result.id, 
                true, 
                true
            );
            setSelectedElement(props);
            setShowProperties(true);
            onElementSelect?.(props);
        }
    };
    
    const handleFitToFrame = () => {
        viewerRef.current?.IFC.fitModelToFrame();
    };
    
    const handleSectionToggle = () => {
        setSectionEnabled(!sectionEnabled);
        // Toggle section plane
    };
    
    const setView = (viewName) => {
        const viewer = viewerRef.current;
        if (!viewer) return;
        
        const views = {
            top: { position: [0, 0, 50], target: [0, 0, 0] },
            front: { position: [0, -50, 0], target: [0, 0, 0] },
            right: { position: [50, 0, 0], target: [0, 0, 0] },
            isometric: { position: [30, 30, 30], target: [0, 0, 0] }
        };
        
        const view = views[viewName];
        if (view) {
            viewer.IFC.context.setCamera(
                new THREE.Vector3(...view.position),
                new THREE.Vector3(...view.target)
            );
        }
    };
    
    return (
        <div style={{ position: 'relative', width, height }}>
            {/* Viewer Container */}
            <div 
                ref={containerRef} 
                style={{ width: '100%', height: '100%' }}
                onDoubleClick={handleDoubleClick}
            />
            
            {/* Loading Overlay */}
            {loading && (
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'rgba(0,0,0,0.5)',
                    color: '#fff'
                }}>
                    Loading IFC Model...
                </div>
            )}
            
            {/* Toolbar */}
            <div style={{
                position: 'absolute',
                top: 10,
                left: 10,
                display: 'flex',
                gap: 5
            }}>
                <button onClick={handleFitToFrame}>Fit</button>
                <button onClick={() => setView('top')}>Top</button>
                <button onClick={() => setView('front')}>Front</button>
                <button onClick={() => setView('isometric')}>3D</button>
                <button onClick={handleSectionToggle}>
                    {sectionEnabled ? 'Hide Section' : 'Section'}
                </button>
                <button onClick={() => setShowProperties(!showProperties)}>
                    Properties
                </button>
            </div>
            
            {/* Properties Panel */}
            {showProperties && selectedElement && (
                <div style={{
                    position: 'absolute',
                    top: 10,
                    right: 10,
                    width: 280,
                    maxHeight: 'calc(100% - 20px)',
                    background: 'rgba(0,0,0,0.85)',
                    borderRadius: 8,
                    padding: 15,
                    color: '#fff',
                    overflow: 'auto'
                }}>
                    <h3 style={{ marginBottom: 10 }}>Properties</h3>
                    <div>
                        <strong>Name:</strong> {selectedElement.Name?.value || 'N/A'}
                    </div>
                    <div>
                        <strong>Type:</strong> {selectedElement.ObjectType?.value || 'N/A'}
                    </div>
                    {/* Add more properties */}
                </div>
            )}
            
            {/* Section Controls */}
            {sectionEnabled && (
                <div style={{
                    position: 'absolute',
                    bottom: 10,
                    left: 10,
                    background: 'rgba(0,0,0,0.8)',
                    padding: 10,
                    borderRadius: 8,
                    color: '#fff'
                }}>
                    <div>Section Plane</div>
                    <input 
                        type="range" 
                        min="-50" 
                        max="50" 
                        value={sectionPosition}
                        onChange={(e) => setSectionPosition(e.target.value)}
                    />
                    <span>{sectionPosition}m</span>
                </div>
            )}
        </div>
    );
};

export default IFCViewer;
'''
    return component
