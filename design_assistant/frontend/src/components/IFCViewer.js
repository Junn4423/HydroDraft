/**
 * IFCViewer Component
 * Trình xem IFC 3D trong trình duyệt (Sprint 4)
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Tooltip,
  Slider,
  Alert,
  CircularProgress,
  Chip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  ThreeDRotation as Rotate3DIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
  ViewInAr as ViewIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  GridOn as GridIcon,
  ContentCut as SectionIcon,
  Download as DownloadIcon,
  Fullscreen as FullscreenIcon,
  Info as InfoIcon,
  TipsAndUpdates as TipsIcon,
} from '@mui/icons-material';

const IFCViewer = ({ ifcUrl, onElementSelect }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [showGrid, setShowGrid] = useState(true);
  const [showSection, setShowSection] = useState(false);
  const [sectionPosition, setSectionPosition] = useState(50);
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedElement, setSelectedElement] = useState(null);

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1500);
    return () => clearTimeout(timer);
  }, [ifcUrl]);

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.2));
  const handleReset = () => setZoom(1);

  const handleViewMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleViewMenuClose = () => {
    setAnchorEl(null);
  };

  // Mock 3D preview with CSS
  const render3DPreview = () => {
    return (
      <Box
        sx={{
          width: '100%',
          height: 400,
          bgcolor: '#1a1a2e',
          borderRadius: 1,
          position: 'relative',
          overflow: 'hidden',
          perspective: 1000,
        }}
      >
        {/* Grid */}
        {showGrid && (
          <Box
            sx={{
              position: 'absolute',
              bottom: 0,
              left: '50%',
              transform: 'translateX(-50%) rotateX(70deg)',
              width: 300 * zoom,
              height: 300 * zoom,
              backgroundImage: 'linear-gradient(#2a2a4e 1px, transparent 1px), linear-gradient(90deg, #2a2a4e 1px, transparent 1px)',
              backgroundSize: '20px 20px',
              opacity: 0.5,
            }}
          />
        )}

        {/* 3D Tank Mock */}
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: `translate(-50%, -50%) scale(${zoom}) rotateX(20deg) rotateY(-30deg)`,
            transformStyle: 'preserve-3d',
            transition: 'transform 0.3s ease',
          }}
        >
          {/* Tank body */}
          <Box
            sx={{
              width: 150,
              height: 80,
              bgcolor: 'rgba(100, 150, 200, 0.8)',
              border: '2px solid #4a90a4',
              borderRadius: 1,
              position: 'relative',
              transformStyle: 'preserve-3d',
              boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
              cursor: 'pointer',
              '&:hover': {
                bgcolor: 'rgba(100, 180, 220, 0.9)',
              },
            }}
            onClick={() => {
              setSelectedElement({
                type: 'IfcTank',
                name: 'Bể lắng 01',
                properties: {
                  Volume: '150 m³',
                  Material: 'Bê tông B25',
                  Dimensions: '10m x 5m x 3m',
                },
              });
            }}
          >
            {/* Water level */}
            <Box
              sx={{
                position: 'absolute',
                bottom: 5,
                left: 5,
                right: 5,
                height: '70%',
                bgcolor: 'rgba(50, 150, 255, 0.5)',
                borderRadius: '0 0 4px 4px',
              }}
            />
            
            {/* Section cut indicator */}
            {showSection && (
              <Box
                sx={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  left: `${sectionPosition}%`,
                  width: 2,
                  bgcolor: 'red',
                  boxShadow: '0 0 10px red',
                }}
              />
            )}
          </Box>

          {/* Inlet pipe */}
          <Box
            sx={{
              position: 'absolute',
              left: -40,
              top: '30%',
              width: 40,
              height: 12,
              bgcolor: '#6b6b6b',
              borderRadius: '6px 0 0 6px',
              transform: 'translateZ(10px)',
            }}
          />

          {/* Outlet pipe */}
          <Box
            sx={{
              position: 'absolute',
              right: -40,
              top: '60%',
              width: 40,
              height: 12,
              bgcolor: '#6b6b6b',
              borderRadius: '0 6px 6px 0',
              transform: 'translateZ(10px)',
            }}
          />
        </Box>

        {/* Loading overlay */}
        {loading && (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: 'rgba(0,0,0,0.7)',
            }}
          >
            <Box sx={{ textAlign: 'center' }}>
              <CircularProgress size={60} />
              <Typography color="white" sx={{ mt: 2 }}>
                Đang tải mô hình 3D...
              </Typography>
            </Box>
          </Box>
        )}

        {/* Axis indicator */}
        <Box
          sx={{
            position: 'absolute',
            bottom: 10,
            left: 10,
            color: 'white',
            fontSize: 12,
          }}
        >
          <Box sx={{ color: 'red' }}>X →</Box>
          <Box sx={{ color: 'green' }}>Y ↑</Box>
          <Box sx={{ color: 'blue' }}>Z ⊙</Box>
        </Box>

        {/* Info chip */}
        <Chip
          size="small"
          label="Demo Preview"
          sx={{ position: 'absolute', top: 10, left: 10 }}
          color="warning"
        />
      </Box>
    );
  };

  return (
    <Paper elevation={0} sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 2 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <ViewIcon color="primary" sx={{ mr: 1 }} />
        <Typography variant="h6">Trình xem 3D</Typography>
        <Chip 
          size="small" 
          label="IFC Viewer" 
          sx={{ ml: 'auto' }} 
          color="primary" 
          variant="outlined"
        />
      </Box>

      {/* Toolbar */}
      <Box sx={{ display: 'flex', gap: 0.5, mb: 1 }}>
        <Tooltip title="Thu nhỏ">
          <IconButton size="small" onClick={handleZoomOut}>
            <ZoomOutIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Phóng to">
          <IconButton size="small" onClick={handleZoomIn}>
            <ZoomInIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Về giữa">
          <IconButton size="small" onClick={handleReset}>
            <CenterIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title={showGrid ? 'Ẩn lưới' : 'Hiện lưới'}>
          <IconButton size="small" onClick={() => setShowGrid(!showGrid)}>
            <GridIcon color={showGrid ? 'primary' : 'inherit'} />
          </IconButton>
        </Tooltip>
        <Tooltip title={showSection ? 'Tắt cắt' : 'Bật cắt'}>
          <IconButton size="small" onClick={() => setShowSection(!showSection)}>
            <SectionIcon color={showSection ? 'primary' : 'inherit'} />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="Chế độ xem">
          <IconButton size="small" onClick={handleViewMenuClick}>
            <Rotate3DIcon />
          </IconButton>
        </Tooltip>
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleViewMenuClose}
        >
          <MenuItem onClick={handleViewMenuClose}>
            <ListItemIcon><VisibilityIcon fontSize="small" /></ListItemIcon>
            <ListItemText>Mặt trước</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleViewMenuClose}>
            <ListItemIcon><VisibilityIcon fontSize="small" /></ListItemIcon>
            <ListItemText>Mặt bên</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleViewMenuClose}>
            <ListItemIcon><VisibilityIcon fontSize="small" /></ListItemIcon>
            <ListItemText>Mặt trên</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleViewMenuClose}>
            <ListItemIcon><Rotate3DIcon fontSize="small" /></ListItemIcon>
            <ListItemText>Isometric</ListItemText>
          </MenuItem>
        </Menu>

        <Box sx={{ flexGrow: 1 }} />

        <Tooltip title="Toàn màn hình">
          <IconButton size="small">
            <FullscreenIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Section slider */}
      {showSection && (
        <Box sx={{ px: 2, mb: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Vị trí mặt cắt: {sectionPosition}%
          </Typography>
          <Slider
            size="small"
            value={sectionPosition}
            onChange={(e, v) => setSectionPosition(v)}
            min={0}
            max={100}
          />
        </Box>
      )}

      {/* 3D Viewer */}
      {error ? (
        <Alert severity="error">{error}</Alert>
      ) : (
        render3DPreview()
      )}

      {/* Selected element info */}
      {selectedElement && (
        <Alert 
          severity="info" 
          sx={{ mt: 2 }}
          icon={<InfoIcon />}
          onClose={() => setSelectedElement(null)}
        >
          <Typography variant="subtitle2">{selectedElement.name}</Typography>
          <Typography variant="caption" display="block">
            Loại: {selectedElement.type}
          </Typography>
          {Object.entries(selectedElement.properties).map(([key, value]) => (
            <Typography key={key} variant="caption" display="block">
              {key}: {value}
            </Typography>
          ))}
        </Alert>
      )}

      {/* Help text */}
      <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
        <TipsIcon fontSize="small" sx={{ mr: 0.5 }} /> Click vào đối tượng để xem thông tin. Kéo để xoay mô hình.
      </Typography>
    </Paper>
  );
};

export default IFCViewer;
