# PyInstaller hook for ezdxf.addons
# This hook excludes all ezdxf addons that require Qt/matplotlib dependencies

from PyInstaller.utils.hooks import collect_submodules, exclude_typestubs

# Exclude all addons to avoid dependency issues
excludedimports = [
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
]
