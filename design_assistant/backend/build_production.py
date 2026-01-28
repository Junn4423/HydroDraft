"""
HydroDraft Production Build Script

Builds standalone Windows executable using PyInstaller
Includes all Sprint 1-4 components

Usage:
    python build_production.py
    
Output:
    dist/HydroDraft.exe (or dist/HydroDraft folder)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


# Build configuration
BUILD_CONFIG = {
    "app_name": "HydroDraft",
    "version": "1.0.0",
    "author": "HydroDraft Team",
    "description": "Professional Engineering Design Platform",
    "icon": None,  # Path to .ico file
    "console": False,  # Set True for debugging
    "onefile": False,  # False = folder, True = single exe (slower startup)
}

# Paths
BASE_DIR = Path(__file__).parent
BACKEND_DIR = BASE_DIR
FRONTEND_BUILD = BASE_DIR.parent / "frontend" / "build"
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"


def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check Python version
    py_version = sys.version_info
    if py_version < (3, 9):
        print(f"❌ Python 3.9+ required (found {py_version.major}.{py_version.minor})")
        return False
    print(f"✅ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Check key dependencies
    required = [
        "fastapi", "uvicorn", "ezdxf", "sqlalchemy", "aiosqlite"
    ]
    
    for pkg in required:
        try:
            __import__(pkg)
            print(f"✅ {pkg}")
        except ImportError:
            print(f"❌ {pkg} not found")
            return False
    
    return True


def build_frontend():
    """Build React frontend"""
    print("\n📦 Building frontend...")
    
    frontend_dir = BASE_DIR.parent / "frontend"
    
    if not frontend_dir.exists():
        print("⚠️ Frontend directory not found, skipping")
        return False
    
    # Check if build already exists
    if (frontend_dir / "build" / "index.html").exists():
        print("✅ Frontend build exists")
        return True
    
    # Run npm build
    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=str(frontend_dir),
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ Frontend built successfully")
            return True
        else:
            print(f"❌ Frontend build failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("⚠️ npm not found, skipping frontend build")
        return False


def copy_static_files():
    """Copy static files to build directory"""
    print("\n📁 Copying static files...")
    
    # Create data directories
    data_dirs = [
        "data",
        "outputs",
        "outputs/reports",
        "outputs/bim",
        "templates",
        "temp"
    ]
    
    for dir_name in data_dirs:
        dir_path = DIST_DIR / BUILD_CONFIG["app_name"] / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created {dir_name}/")
    
    # Copy rules
    rules_src = BACKEND_DIR / "rules" / "definitions"
    rules_dst = DIST_DIR / BUILD_CONFIG["app_name"] / "rules" / "definitions"
    if rules_src.exists():
        shutil.copytree(rules_src, rules_dst, dirs_exist_ok=True)
        print("✅ Copied rules/")
    
    # Copy templates
    templates_src = BACKEND_DIR / "templates"
    templates_dst = DIST_DIR / BUILD_CONFIG["app_name"] / "templates"
    if templates_src.exists():
        for f in templates_src.glob("*.json"):
            shutil.copy(f, templates_dst)
        print("✅ Copied templates/")
    
    # Copy frontend build
    if FRONTEND_BUILD.exists():
        frontend_dst = DIST_DIR / BUILD_CONFIG["app_name"] / "static"
        shutil.copytree(FRONTEND_BUILD, frontend_dst, dirs_exist_ok=True)
        print("✅ Copied frontend build to static/")


def generate_spec_file():
    """Generate PyInstaller spec file"""
    print("\n📝 Generating spec file...")
    
    # Hidden imports for dynamic modules
    hidden_imports = [
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "aiosqlite",
        "sqlalchemy.dialects.sqlite",
        "ezdxf",
        "numpy",
        "pydantic",
        "starlette",
        "anyio._backends._asyncio",
        # ReportLab for PDF generation
        "reportlab",
        "reportlab.lib",
        "reportlab.lib.colors",
        "reportlab.lib.pagesizes",
        "reportlab.lib.styles",
        "reportlab.lib.units",
        "reportlab.lib.enums",
        "reportlab.platypus",
        "reportlab.pdfbase",
        "reportlab.pdfbase.ttfonts",
        "reportlab.pdfgen",
        # Pillow (required by reportlab)
        "PIL",
        "PIL.Image",
        "PIL.ImageFont",
        "PIL.ImageDraw",
        "PIL.PngImagePlugin",
        "PIL.JpegImagePlugin",
        # ============================================
        # pkg_resources / setuptools dependencies
        # These are required to avoid runtime ImportError
        # ============================================
        # jaraco packages
        "jaraco",
        "jaraco.text",
        "jaraco.functools", 
        "jaraco.context",
        "jaraco.collections",
        # platformdirs
        "platformdirs",
        # more-itertools
        "more_itertools",
        "more_itertools.more",
        "more_itertools.recipes",
        # backports
        "backports",
        "backports.tarfile",
        # importlib resources/metadata
        "importlib_resources",
        "importlib_metadata",
        # packaging
        "packaging",
        "packaging.version",
        "packaging.specifiers",
        "packaging.requirements",
        "packaging.markers",
        "packaging.utils",
        "packaging.tags",
        "packaging.metadata",
        # zipp
        "zipp",
        # typing extensions
        "typing_extensions",
    ]
    
    # Data files
    datas = [
        (str(BACKEND_DIR / "rules"), "rules"),
        (str(BACKEND_DIR / "templates"), "templates"),
    ]

    if FRONTEND_BUILD.exists():
        datas.append((str(FRONTEND_BUILD), "static"))
    
    # Generate spec content
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# HydroDraft PyInstaller Spec File
# Generated: {datetime.now().isoformat()}

import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Hidden imports - manually specified to avoid bytecode scan issues on Python 3.10.0
hiddenimports = {hidden_imports}
# Selectively add ezdxf modules (avoid browser addon that requires Qt)
hiddenimports += [
    'ezdxf',
    'ezdxf.entities',
    'ezdxf.entities.dxfns',
    'ezdxf.entities.dxfgfx',
    'ezdxf.entities.dxfobj',
    'ezdxf.layouts',
    'ezdxf.layouts.layouts',
    'ezdxf.math',
    'ezdxf.math._vector',
    'ezdxf.math._matrix44',
    'ezdxf.tools',
    'ezdxf.tools.standards',
    'ezdxf.sections',
    'ezdxf.sections.header',
    'ezdxf.sections.tables',
    'ezdxf.sections.blocks',
    'ezdxf.sections.classes',
    'ezdxf.sections.objects',
    'ezdxf.sections.entities',
    'ezdxf.query',
    'ezdxf.groupby',
    'ezdxf.units',
    'ezdxf.enums',
    'ezdxf.lldxf',
    'ezdxf.lldxf.tagwriter',
    'ezdxf.lldxf.loader',
    'ezdxf.lldxf.validator',
    'ezdxf.audit',
    'ezdxf.document',
    'ezdxf.filemanagement',
]
# Manually add required sqlalchemy modules
hiddenimports += [
    'sqlalchemy',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.ext.asyncio',
    'sqlalchemy.orm',
    'sqlalchemy.sql',
]

# Data files
datas = {datas}
datas += collect_data_files('PIL')
datas += collect_data_files('ezdxf')

a = Analysis(
    ['main.py'],
    pathex=['{str(BACKEND_DIR).replace(chr(92), chr(92)+chr(92))}'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['{str(BACKEND_DIR).replace(chr(92), chr(92)+chr(92))}\\\\hooks'],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'cv2',
        'PyQt5',
        'PyQt6',
        'PySide6',
        # Exclude all ezdxf.addons - they require Qt/matplotlib and are not needed for basic DXF generation
        'ezdxf.addons',
        'ezdxf.addons.browser',
        'ezdxf.addons.drawing', 
        'ezdxf.addons.geo',
        'ezdxf.addons.mtxpl',
        'ezdxf.addons.text2path',
        'ezdxf.addons.r12export',
        'ezdxf.addons.odafc',
        'ezdxf.addons.hpgl2',
        'ezdxf.addons.dwg',
        'ezdxf.addons.dxf2code',
        'ezdxf.addons.importer',
        'ezdxf.addons.meshex',
        'ezdxf.addons.acadctb',
        'ezdxf.addons.iterdxf',
        'ezdxf.addons.openscad',
        'ezdxf.addons.pycsg',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'sphinx',
        # Exclude modules causing bytecode issues in Python 3.10.0
        'setuptools._vendor',
        'pkg_resources._vendor',
        'pip._vendor',
        'pip._internal',
        'distutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    module_collection_mode={{'setuptools': 'py', 'pkg_resources': 'py'}},
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{BUILD_CONFIG["app_name"]}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={BUILD_CONFIG["console"]},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={repr(BUILD_CONFIG["icon"]) if BUILD_CONFIG["icon"] else None},
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{BUILD_CONFIG["app_name"]}',
)
'''
    
    spec_path = BACKEND_DIR / "HydroDraft_build.spec"
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✅ Spec file: {spec_path}")
    return spec_path


def run_pyinstaller(spec_path):
    """Run PyInstaller"""
    print("\n🔨 Running PyInstaller...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_path)
    ]
    
    result = subprocess.run(cmd, cwd=str(BACKEND_DIR))
    
    return result.returncode == 0


def create_run_script():
    """Create run script in dist folder"""
    print("\n📜 Creating run script...")
    
    bat_content = f'''@echo off
title HydroDraft - Professional Engineering Platform
echo.
echo ====================================================
echo   HydroDraft v{BUILD_CONFIG["version"]}
echo   Professional Engineering Design Platform
echo ====================================================
echo.
echo Starting server...
echo.
cd /d "%~dp0"
start "" "http://localhost:8000"
"{BUILD_CONFIG["app_name"]}.exe"
pause
'''
    
    bat_path = DIST_DIR / BUILD_CONFIG["app_name"] / f"Run_{BUILD_CONFIG['app_name']}.bat"
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    
    print(f"✅ Created {bat_path.name}")


def create_readme():
    """Create README in dist folder"""
    readme_content = f'''# HydroDraft v{BUILD_CONFIG["version"]}

## Professional Engineering Design Platform

### Quick Start

1. Double-click `Run_HydroDraft.bat` to start
2. Browser will open automatically at http://localhost:8000
3. Access API docs at http://localhost:8000/docs

### Features

**Sprint 1 - Offline Foundation**
- SQLite database (no external DB required)
- Standalone Windows application
- Auto browser launch

**Sprint 2 - Engineering Core**  
- Traceable calculations with LaTeX formulas
- TCVN standard compliance
- Safety violation detection

**Sprint 3 - Professional CAD**
- DXF export with 49 TCVN-compliant layers
- Block library (valves, manholes, pumps)
- Structural rebar detailing
- Dimension and annotation standards

**Sprint 4 - BIM & Enterprise**
- BIM data export (Revit/Dynamo/pyRevit)
- Version control for designs
- PDF technical reports
- 3D viewer configuration

### System Requirements

- Windows 10/11
- 4GB RAM minimum
- 500MB disk space
- Web browser (Chrome/Edge recommended)

### Folder Structure

```
HydroDraft/
├── HydroDraft.exe      # Main application
├── Run_HydroDraft.bat  # Start script
├── data/               # Database files
├── outputs/            # Generated files
│   ├── reports/        # PDF reports
│   └── bim/           # BIM exports
├── rules/             # Design rules
├── templates/         # Design templates
└── static/            # Web interface
```

### Troubleshooting

**Port already in use:**
Change port in config or close other applications using port 8000.

**Database errors:**
Delete `data/design_data.db` to reset database.

**Missing dependencies:**
Ensure all files are extracted from the distribution.

### Support

Generated by HydroDraft Build System
Build Date: {datetime.now().strftime("%Y-%m-%d")}
'''
    
    readme_path = DIST_DIR / BUILD_CONFIG["app_name"] / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ Created README.md")


def main():
    """Main build process"""
    print("=" * 60)
    print(f"  🏗️ HydroDraft Production Build")
    print(f"  Version: {BUILD_CONFIG['version']}")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed!")
        return False
    
    # Build frontend (optional)
    build_frontend()
    
    # Generate spec file
    spec_path = generate_spec_file()
    
    # Run PyInstaller
    if not run_pyinstaller(spec_path):
        print("\n❌ PyInstaller build failed!")
        return False
    
    # Copy additional files
    copy_static_files()
    
    # Create helper scripts
    create_run_script()
    create_readme()
    
    # Summary
    elapsed = datetime.now() - start_time
    dist_path = DIST_DIR / BUILD_CONFIG["app_name"]
    
    print("\n" + "=" * 60)
    print("  ✅ BUILD SUCCESSFUL!")
    print("=" * 60)
    print(f"  Output: {dist_path}")
    print(f"  Time: {elapsed.total_seconds():.1f}s")
    print("\n  To run: Double-click Run_HydroDraft.bat")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
