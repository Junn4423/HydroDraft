import React, { useRef, useEffect, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
  ButtonGroup,
  Button,
} from '@mui/material';
import {
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Fullscreen as FullscreenIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Image as ImageIcon,
} from '@mui/icons-material';

/**
 * DXF Preview Component - Mô phỏng bản vẽ CAD trên canvas
 * 
 * Props:
 * - dimensions: Kích thước bể/công trình
 * - type: 'tank' | 'pipeline' | 'well'
 * - drawingData: Dữ liệu để vẽ
 */
const DXFPreview = ({
  dimensions,
  type = 'tank',
  drawingData,
  downloadUrl,
  title = 'Preview bản vẽ',
}) => {
  const canvasRef = useRef(null);
  const [zoom, setZoom] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Scale factor để vẽ
  const SCALE = 20; // 20 pixels per meter

  useEffect(() => {
    if (dimensions || drawingData) {
      drawPreview();
    }
  }, [dimensions, drawingData, zoom]);

  const drawPreview = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, width, height);

    // Set up coordinate system
    ctx.save();
    ctx.translate(width / 2, height / 2);
    ctx.scale(zoom, -zoom); // Flip Y axis for CAD-style

    // Draw grid
    drawGrid(ctx, width, height);

    // Draw based on type
    switch (type) {
      case 'tank':
        drawTankPreview(ctx);
        break;
      case 'pipeline':
        drawPipelinePreview(ctx);
        break;
      case 'well':
        drawWellPreview(ctx);
        break;
      default:
        break;
    }

    ctx.restore();

    // Draw legend and scale bar
    drawLegend(ctx, width, height);
  };

  const drawGrid = (ctx, width, height) => {
    ctx.strokeStyle = '#2a2a4e';
    ctx.lineWidth = 0.5;
    ctx.setLineDash([2, 2]);

    const gridSize = SCALE; // 1 meter grid
    const gridRange = Math.max(width, height) / zoom;

    for (let x = -gridRange; x <= gridRange; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, -gridRange);
      ctx.lineTo(x, gridRange);
      ctx.stroke();
    }

    for (let y = -gridRange; y <= gridRange; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(-gridRange, y);
      ctx.lineTo(gridRange, y);
      ctx.stroke();
    }

    ctx.setLineDash([]);
  };

  const drawTankPreview = (ctx) => {
    if (!dimensions) return;

    const { length = 10, width: tankWidth = 5, depth = 3, total_depth = 4 } = dimensions;
    const wallThickness = 0.25;

    // Scale dimensions
    const L = length * SCALE;
    const W = tankWidth * SCALE;
    const D = (total_depth || depth) * SCALE;
    const wall = wallThickness * SCALE;

    // Draw plan view (top)
    const planY = D / 2 + 30;

    // Outer walls
    ctx.fillStyle = '#4a5568';
    ctx.fillRect(-L / 2 - wall, planY - W / 2 - wall, L + 2 * wall, W + 2 * wall);

    // Inner (water area)
    ctx.fillStyle = '#63b3ed';
    ctx.fillRect(-L / 2, planY - W / 2, L, W);

    // Labels for plan
    ctx.save();
    ctx.scale(1, -1);
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(`MẶT BẰNG`, 0, -(planY + W / 2 + 15));
    ctx.fillText(`${length} m`, 0, -(planY - W / 2 - 5));
    ctx.restore();

    // Draw section view (bottom)
    const sectionY = -D / 2 - 30;

    // Draw section outline
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.rect(-L / 2 - wall, sectionY - D - wall, L + 2 * wall, D + wall);
    ctx.stroke();

    // Fill walls
    ctx.fillStyle = '#4a5568';
    // Left wall
    ctx.fillRect(-L / 2 - wall, sectionY - D - wall, wall, D + wall);
    // Right wall
    ctx.fillRect(L / 2, sectionY - D - wall, wall, D + wall);
    // Bottom
    ctx.fillRect(-L / 2 - wall, sectionY - D - wall, L + 2 * wall, wall);

    // Water level
    const waterDepth = depth * SCALE;
    ctx.fillStyle = 'rgba(99, 179, 237, 0.5)';
    ctx.fillRect(-L / 2, sectionY - waterDepth, L, waterDepth);

    // Water surface pattern
    ctx.strokeStyle = '#63b3ed';
    ctx.lineWidth = 1;
    for (let x = -L / 2 + 10; x < L / 2; x += 20) {
      ctx.beginPath();
      ctx.moveTo(x, sectionY);
      ctx.bezierCurveTo(x + 5, sectionY + 3, x + 10, sectionY - 3, x + 15, sectionY);
      ctx.stroke();
    }

    // Labels for section
    ctx.save();
    ctx.scale(1, -1);
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(`MẶT CẮT`, 0, -sectionY + 15);
    ctx.textAlign = 'right';
    ctx.fillText(`${depth} m`, -L / 2 - wall - 5, -(sectionY - waterDepth / 2));
    ctx.restore();

    // Dimension lines
    drawDimensionLine(ctx, -L / 2, planY + W / 2 + 20, L / 2, planY + W / 2 + 20, `${length} m`);
    drawDimensionLine(ctx, -L / 2 - wall - 15, planY - W / 2, -L / 2 - wall - 15, planY + W / 2, `${tankWidth} m`, true);
  };

  const drawPipelinePreview = (ctx) => {
    if (!drawingData?.segments) return;

    const segments = drawingData.segments;
    const totalLength = drawingData.total_length || 100;
    const xScale = 300 / totalLength; // Fit into canvas

    // Draw ground profile
    ctx.strokeStyle = '#8b5a2b';
    ctx.lineWidth = 2;
    ctx.beginPath();

    segments.forEach((seg, i) => {
      const x1 = (seg.start_station || i * 50) * xScale - 150;
      const groundLevel = (seg.ground_start || 10) * SCALE - 200;

      if (i === 0) {
        ctx.moveTo(x1, groundLevel);
      }
      const x2 = (seg.end_station || (i + 1) * 50) * xScale - 150;
      const groundEnd = (seg.ground_end || 10) * SCALE - 200;
      ctx.lineTo(x2, groundEnd);
    });
    ctx.stroke();

    // Draw pipe
    ctx.strokeStyle = '#4299e1';
    ctx.lineWidth = 3;
    ctx.beginPath();

    segments.forEach((seg, i) => {
      const x1 = (seg.start_station || i * 50) * xScale - 150;
      const x2 = (seg.end_station || (i + 1) * 50) * xScale - 150;
      const invertStart = (seg.invert_start || 8) * SCALE - 200;
      const invertEnd = (seg.invert_end || 7.5) * SCALE - 200;

      if (i === 0) ctx.moveTo(x1, invertStart);
      ctx.lineTo(x2, invertEnd);

      // Draw manhole
      ctx.fillStyle = '#718096';
      ctx.fillRect(x1 - 5, invertStart, 10, ((seg.ground_start || 10) - (seg.invert_start || 8)) * SCALE);
    });
    ctx.stroke();

    // Labels
    ctx.save();
    ctx.scale(1, -1);
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(`TRẮC DỌC TUYẾN ỐNG - Tổng chiều dài: ${totalLength} m`, 0, 150);
    ctx.restore();
  };

  const drawWellPreview = (ctx) => {
    if (!drawingData?.design) return;

    const { total_depth = 30, casing_diameter = 110, borehole_diameter = 210 } = drawingData.design;
    const structure = drawingData.structure || {};
    const screenTop = structure.screen?.depth_from || total_depth * 0.7;
    const screenBottom = structure.screen?.depth_to || total_depth;

    const scale = 3; // Vertical scale
    const hScale = 0.5; // Horizontal scale for diameter

    // Draw borehole
    const boreholeWidth = borehole_diameter * hScale / 10;
    ctx.fillStyle = '#5d4e37';
    ctx.fillRect(-boreholeWidth / 2, -total_depth * scale + 250, boreholeWidth, total_depth * scale);

    // Draw grout/cement
    ctx.fillStyle = '#718096';
    ctx.fillRect(-boreholeWidth / 2, -screenTop * scale + 250, boreholeWidth, screenTop * scale);

    // Draw gravel pack
    ctx.fillStyle = '#c4b28f';
    ctx.fillRect(-boreholeWidth / 2, -(screenBottom) * scale + 250, boreholeWidth, (screenBottom - screenTop + 2) * scale);

    // Draw casing
    const casingWidth = casing_diameter * hScale / 10;
    ctx.fillStyle = '#3182ce';
    ctx.fillRect(-casingWidth / 2, -screenTop * scale + 250, casingWidth, screenTop * scale);

    // Draw screen (with slots)
    ctx.fillStyle = '#4299e1';
    ctx.fillRect(-casingWidth / 2, -(screenBottom) * scale + 250, casingWidth, (screenBottom - screenTop) * scale);

    // Draw screen slots
    ctx.strokeStyle = '#1a202c';
    ctx.lineWidth = 1;
    for (let y = screenTop; y < screenBottom; y += 1) {
      const slotY = -y * scale + 250;
      ctx.beginPath();
      ctx.moveTo(-casingWidth / 2, slotY);
      ctx.lineTo(casingWidth / 2, slotY);
      ctx.stroke();
    }

    // Draw protective casing
    const protWidth = (casing_diameter + 50) * hScale / 10;
    ctx.fillStyle = '#2d3748';
    ctx.fillRect(-protWidth / 2, 250, protWidth, 15);

    // Ground surface
    ctx.fillStyle = '#48bb78';
    ctx.fillRect(-100, 248, 200, 5);

    // Labels
    ctx.save();
    ctx.scale(1, -1);
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '11px Arial';
    ctx.textAlign = 'left';
    ctx.fillText(`Ống chống Ø${casing_diameter}`, 40, -(250 - screenTop * scale / 2));
    ctx.fillText(`Ống lọc Ø${casing_diameter}`, 40, -(250 - (screenTop + screenBottom) * scale / 2));
    ctx.fillText(`Sỏi lọc`, 40, -(250 - screenBottom * scale + 10));
    ctx.fillText(`Tổng sâu: ${total_depth}m`, 40, -(250 - total_depth * scale - 10));
    ctx.textAlign = 'center';
    ctx.fillText(`MẶT CẮT GIẾNG QUAN TRẮC`, 0, -280);
    ctx.restore();
  };

  const drawDimensionLine = (ctx, x1, y1, x2, y2, text, vertical = false) => {
    ctx.strokeStyle = '#a0aec0';
    ctx.lineWidth = 1;

    // Main line
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();

    // End ticks
    const tickSize = 5;
    if (vertical) {
      ctx.beginPath();
      ctx.moveTo(x1 - tickSize, y1);
      ctx.lineTo(x1 + tickSize, y1);
      ctx.moveTo(x2 - tickSize, y2);
      ctx.lineTo(x2 + tickSize, y2);
      ctx.stroke();
    } else {
      ctx.beginPath();
      ctx.moveTo(x1, y1 - tickSize);
      ctx.lineTo(x1, y1 + tickSize);
      ctx.moveTo(x2, y2 - tickSize);
      ctx.lineTo(x2, y2 + tickSize);
      ctx.stroke();
    }

    // Text
    ctx.save();
    ctx.scale(1, -1);
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '10px Arial';
    ctx.textAlign = 'center';
    if (vertical) {
      ctx.fillText(text, x1 - 20, -(y1 + y2) / 2);
    } else {
      ctx.fillText(text, (x1 + x2) / 2, -(y1 + 10));
    }
    ctx.restore();
  };

  const drawLegend = (ctx, width, height) => {
    ctx.fillStyle = 'rgba(26, 26, 46, 0.8)';
    ctx.fillRect(10, 10, 120, 70);

    ctx.strokeStyle = '#4a5568';
    ctx.lineWidth = 1;
    ctx.strokeRect(10, 10, 120, 70);

    ctx.fillStyle = '#e2e8f0';
    ctx.font = '10px Arial';
    ctx.fillText('CHÚ THÍCH:', 20, 28);

    // Legend items based on type
    if (type === 'tank') {
      ctx.fillStyle = '#4a5568';
      ctx.fillRect(20, 38, 15, 10);
      ctx.fillStyle = '#e2e8f0';
      ctx.fillText('Bê tông', 45, 47);

      ctx.fillStyle = '#63b3ed';
      ctx.fillRect(20, 55, 15, 10);
      ctx.fillStyle = '#e2e8f0';
      ctx.fillText('Vùng nước', 45, 64);
    } else if (type === 'well') {
      ctx.fillStyle = '#3182ce';
      ctx.fillRect(20, 38, 15, 10);
      ctx.fillStyle = '#e2e8f0';
      ctx.fillText('Ống chống', 45, 47);

      ctx.fillStyle = '#c4b28f';
      ctx.fillRect(20, 55, 15, 10);
      ctx.fillStyle = '#e2e8f0';
      ctx.fillText('Sỏi lọc', 45, 64);
    }

    // Scale bar
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '9px Arial';
    ctx.fillText(`Zoom: ${(zoom * 100).toFixed(0)}%`, width - 80, height - 10);
  };

  const handleZoomIn = () => setZoom((z) => Math.min(z * 1.2, 3));
  const handleZoomOut = () => setZoom((z) => Math.max(z / 1.2, 0.3));
  const handleReset = () => setZoom(1);

  return (
    <Paper sx={{ p: 2, bgcolor: '#1a1a2e' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="subtitle1" color="grey.300" sx={{ display: 'flex', alignItems: 'center' }}>
          <ImageIcon fontSize="small" sx={{ mr: 1 }} /> {title}
        </Typography>
        <Box>
          <ButtonGroup size="small" variant="outlined">
            <Tooltip title="Phóng to">
              <Button onClick={handleZoomIn}>
                <ZoomInIcon fontSize="small" />
              </Button>
            </Tooltip>
            <Tooltip title="Thu nhỏ">
              <Button onClick={handleZoomOut}>
                <ZoomOutIcon fontSize="small" />
              </Button>
            </Tooltip>
            <Tooltip title="Reset">
              <Button onClick={handleReset}>
                <RefreshIcon fontSize="small" />
              </Button>
            </Tooltip>
          </ButtonGroup>
          {downloadUrl && (
            <Tooltip title="Tải DXF">
              <IconButton size="small" href={downloadUrl} sx={{ ml: 1, color: 'primary.main' }}>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'center', bgcolor: '#1a1a2e', borderRadius: 1 }}>
        <canvas
          ref={canvasRef}
          width={500}
          height={400}
          style={{ border: '1px solid #4a5568', borderRadius: 4 }}
        />
      </Box>

      {(dimensions || drawingData) && (
        <Typography variant="caption" color="grey.500" sx={{ display: 'block', mt: 1, textAlign: 'center' }}>
          Nhấp và kéo để di chuyển, cuộn để zoom • Tỷ lệ 1:{Math.round(50 / zoom)}
        </Typography>
      )}
    </Paper>
  );
};

export default DXFPreview;
