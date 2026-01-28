import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  Chip,
  Slider,
  Tooltip,
  Collapse,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
import {
  Calculate as CalculateIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Info as InfoIcon,
  Pool as PoolIcon,
  Opacity as WaterDropIcon,
  Balance as BalanceIcon,
  FilterAlt as FilterIcon,
  Assignment as AssignmentIcon,
  Settings as SettingsIcon,
  Straighten as StraightenIcon,
  TipsAndUpdates as TipsAndUpdatesIcon,
  CheckCircle as CheckCircleIcon,
  Engineering as EngineeringIcon,
  Architecture as ArchitectureIcon,
  Draw as DrawIcon,
  Functions as FunctionsIcon,
  Pending as PendingIcon,
} from '@mui/icons-material';
import axios from 'axios';
import DXFPreview from '../components/DXFPreview';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const tankTypes = [
  { value: 'sedimentation', label: 'Bể lắng', iconComponent: PoolIcon },
  { value: 'storage', label: 'Bể chứa', iconComponent: WaterDropIcon },
  { value: 'buffer', label: 'Bể điều hòa', iconComponent: BalanceIcon },
  { value: 'filtration', label: 'Bể lọc', iconComponent: FilterIcon },
];

const designGuides = {
  sedimentation: {
    detention_time: { min: 1.5, max: 4, unit: 'giờ', desc: 'Thời gian lưu nước trong bể' },
    surface_loading_rate: { min: 20, max: 40, unit: 'm³/m²/ngày', desc: 'Tải trọng bề mặt' },
    depth: { min: 2.5, max: 5, unit: 'm', desc: 'Chiều sâu nước' },
  },
  storage: {
    detention_time: { min: 4, max: 12, unit: 'giờ', desc: 'Thời gian trữ nước' },
    depth: { min: 3, max: 6, unit: 'm', desc: 'Chiều sâu nước' },
  },
  buffer: {
    detention_time: { min: 2, max: 8, unit: 'giờ', desc: 'Thời gian điều hòa' },
    depth: { min: 3, max: 5, unit: 'm', desc: 'Chiều sâu nước' },
  },
  filtration: {
    surface_loading_rate: { min: 5, max: 12, unit: 'm³/m²/h', desc: 'Tải trọng lọc' },
    detention_time: { min: 0.3, max: 1, unit: 'giờ', desc: 'Thời gian lọc' },
    depth: { min: 1.5, max: 3, unit: 'm', desc: 'Chiều sâu lớp lọc' },
  },
};

function TankDesignPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [formData, setFormData] = useState({
    project_name: '',
    tank_name: '',
    tank_type: 'sedimentation',
    flow_rate: 1000,
    detention_time: 2.0,
    surface_loading_rate: 35,
    depth: 3.0,
    number_of_tanks: 2,
    length_width_ratio: 3.0,
    wall_thickness: 0.25,
    bottom_thickness: 0.3,
    generate_drawing: true,
  });

  const [loading, setLoading] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [result, setResult] = useState(null);
  const [previewDimensions, setPreviewDimensions] = useState(null);
  const [error, setError] = useState(null);
  const [recentDesigns, setRecentDesigns] = useState([]);
  
  // Progress tracking state
  const [progressOpen, setProgressOpen] = useState(false);
  const [progressStep, setProgressStep] = useState(0);
  const [progressSteps, setProgressSteps] = useState([
    { label: 'Kiểm tra đầu vào', formula: '', status: 'pending', detail: '' },
    { label: 'Tính toán thể tích', formula: 'V = Q × t / 24', status: 'pending', detail: '' },
    { label: 'Tính kích thước bể', formula: 'L:W:H theo tỷ lệ thiết kế', status: 'pending', detail: '' },
    { label: 'Kiểm tra thủy lực', formula: 'SLR = Q / A', status: 'pending', detail: '' },
    { label: 'Tính kết cấu', formula: 'σ ≤ [σ] theo TCVN', status: 'pending', detail: '' },
    { label: 'Tạo bản vẽ DXF', formula: '', status: 'pending', detail: '' },
  ]);

  // Load recent designs from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('recentTankDesigns');
    if (saved) {
      setRecentDesigns(JSON.parse(saved));
    }
  }, []);

  // Calculate preview dimensions
  const calculatePreview = useCallback(() => {
    // Quick calculation for preview
    const Q = formData.flow_rate / formData.number_of_tanks; // m³/ngày per tank
    const HRT = formData.detention_time; // giờ
    const V = (Q * HRT) / 24; // m³ per tank
    const depth = formData.depth || 3;
    const A = V / depth; // m²
    const ratio = formData.length_width_ratio || 3;
    const W = Math.sqrt(A / ratio);
    const L = W * ratio;

    setPreviewDimensions({
      length: Math.round(L * 10) / 10,
      width: Math.round(W * 10) / 10,
      depth: depth,
      total_depth: depth + 0.8, // freeboard + sludge
      volume: Math.round(V),
      surface_area: Math.round(A * 10) / 10,
    });
  }, [formData.flow_rate, formData.number_of_tanks, formData.detention_time, formData.depth, formData.length_width_ratio]);

  // Real-time preview calculation - triggers whenever input changes
  useEffect(() => {
    const timer = setTimeout(() => {
      if (formData.flow_rate > 0 && formData.detention_time > 0) {
        calculatePreview();
      }
    }, 300); // Reduced delay for faster feedback
    return () => clearTimeout(timer);
  }, [calculatePreview, formData.flow_rate, formData.detention_time, formData.depth, formData.number_of_tanks, formData.length_width_ratio, formData.surface_loading_rate]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    let newValue = type === 'checkbox' ? checked : value;
    
    // Parse numbers
    if (type === 'number' && value !== '') {
      newValue = parseFloat(value);
    }

    setFormData((prev) => ({
      ...prev,
      [name]: newValue,
    }));
  };

  const handleSliderChange = (name) => (e, value) => {
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setProgressOpen(true);
    setProgressStep(0);
    
    // Reset progress steps
    const newSteps = [
      { 
        label: 'Kiểm tra đầu vào', 
        formula: '', 
        status: 'active', 
        detail: `Q = ${formData.flow_rate} m³/ngày, t = ${formData.detention_time} giờ` 
      },
      { 
        label: 'Tính toán thể tích', 
        formula: 'V = Q × t / 24', 
        status: 'pending', 
        detail: '' 
      },
      { 
        label: 'Tính kích thước bể', 
        formula: 'L = √(V×r/H), W = L/r', 
        status: 'pending', 
        detail: '' 
      },
      { 
        label: 'Kiểm tra thủy lực', 
        formula: 'SLR = Q / (L×W), HRT = V/Q', 
        status: 'pending', 
        detail: '' 
      },
      { 
        label: 'Tính kết cấu BTCT', 
        formula: 'M = γ×H²×L/2, As = M/(0.9×d×fy)', 
        status: 'pending', 
        detail: '' 
      },
      { 
        label: 'Tạo bản vẽ DXF', 
        formula: '', 
        status: 'pending', 
        detail: '' 
      },
    ];
    setProgressSteps(newSteps);

    // Simulate progress animation
    const simulateProgress = async () => {
      for (let i = 0; i < 6; i++) {
        await new Promise(resolve => setTimeout(resolve, 300));
        setProgressStep(i);
        setProgressSteps(prev => prev.map((step, idx) => ({
          ...step,
          status: idx < i ? 'completed' : idx === i ? 'active' : 'pending'
        })));
      }
    };
    
    // Start progress simulation
    simulateProgress();

    try {
      const response = await axios.post(
        `${API_URL}/api/v1/design/tank/?_t=${Date.now()}`,
        formData,
        {
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
          },
        }
      );
      
      // Update final progress steps with actual calculation details
      const V_total = (formData.flow_rate * formData.detention_time / 24).toFixed(1);
      const V_per_tank = (V_total / formData.number_of_tanks).toFixed(1);
      const dims = response.data.dimensions || {};
      const hyd = response.data.hydraulic_results || {};
      
      setProgressSteps(prev => prev.map((step, idx) => {
        let detail = step.detail;
        let status = 'completed';
        
        switch(idx) {
          case 0:
            detail = `✓ Q = ${formData.flow_rate} m³/ngày, t = ${formData.detention_time} giờ, n = ${formData.number_of_tanks} bể`;
            break;
          case 1:
            detail = `✓ V tổng = ${V_total} m³, V mỗi bể = ${V_per_tank} m³`;
            break;
          case 2:
            detail = `✓ L = ${dims.length}m, W = ${dims.width}m, H = ${dims.depth}m`;
            break;
          case 3:
            detail = `✓ SLR = ${hyd.surface_loading} m³/m²/ngày, HRT = ${hyd.retention_time} giờ`;
            break;
          case 4:
            detail = response.data.structural_results 
              ? `✓ Bê tông: ${response.data.quantities?.concrete?.toFixed(1)}m³, Thép: ${response.data.quantities?.reinforcement?.toFixed(0)}kg`
              : '✓ Hoàn thành tính kết cấu';
            break;
          case 5:
            detail = response.data.drawing_file ? '✓ Đã tạo file DXF' : '✓ Hoàn thành';
            break;
          default:
            break;
        }
        
        return { ...step, detail, status };
      }));
      
      setResult(response.data);

      // Save to recent designs
      const newDesign = {
        id: response.data.job_id,
        name: formData.tank_name,
        type: formData.tank_type,
        date: new Date().toISOString(),
        dimensions: response.data.dimensions,
      };
      const updated = [newDesign, ...recentDesigns.slice(0, 9)];
      setRecentDesigns(updated);
      localStorage.setItem('recentTankDesigns', JSON.stringify(updated));

      setActiveTab(1); // Switch to results tab
      
      // Close progress dialog after a short delay to show completion
      setTimeout(() => setProgressOpen(false), 800);
    } catch (err) {
      setProgressOpen(false);
      const errorDetail = err.response?.data?.detail;
      if (Array.isArray(errorDetail)) {
        const messages = errorDetail.map((e) =>
          typeof e === 'object' ? e.msg || e.message || JSON.stringify(e) : e
        ).join('; ');
        setError(messages);
      } else if (typeof errorDetail === 'object') {
        setError(errorDetail.msg || errorDetail.message || JSON.stringify(errorDetail));
      } else {
        setError(errorDetail || 'Có lỗi xảy ra khi thiết kế');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleQuickCalc = async () => {
    setCalculating(true);
    setError(null);
    try {
      // Add timestamp to prevent caching
      const response = await axios.post(
        `${API_URL}/api/v1/design/tank/calculate?_t=${Date.now()}`,
        {
          ...formData,
          generate_drawing: false,
        },
        {
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
          },
        }
      );
      setResult(response.data);
      setActiveTab(1);
    } catch (err) {
      setError(err.response?.data?.detail || 'Lỗi tính toán');
    } finally {
      setCalculating(false);
    }
  };

  const getGuide = (param) => {
    return designGuides[formData.tank_type]?.[param] || {};
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <PoolIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h5">Thiết kế Bể</Typography>
        </Box>
        <Chip
          label={tankTypes.find((t) => t.value === formData.tank_type)?.label}
          color="primary"
          variant="outlined"
        />
      </Box>

      <Grid container spacing={3}>
        {/* Left Panel - Input Form */}
        <Grid item xs={12} md={5}>
          <Card>
            <CardContent>
              <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ mb: 2 }}>
                <Tab label="Nhập liệu" />
                <Tab label="Kết quả" disabled={!result} />
                <Tab label="Lịch sử" />
              </Tabs>

              {activeTab === 0 && (
              <Box component="form" onSubmit={handleSubmit}>
                {/* Basic Info */}
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <AssignmentIcon fontSize="small" sx={{ mr: 0.5, color: 'primary.main' }} />
                  <Typography variant="subtitle2" color="primary">
                    Thông tin cơ bản
                  </Typography>
                </Box>
                <TextField
                  fullWidth
                  label="Tên dự án"
                  name="project_name"
                  value={formData.project_name}
                  onChange={handleChange}
                  margin="dense"
                  size="small"
                  required
                />
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Ký hiệu bể"
                      name="tank_name"
                      value={formData.tank_name}
                      onChange={handleChange}
                      margin="dense"
                      size="small"
                      required
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <FormControl fullWidth margin="dense" size="small">
                      <InputLabel>Loại bể</InputLabel>
                      <Select
                        name="tank_type"
                        value={formData.tank_type}
                        label="Loại bể"
                        onChange={handleChange}
                      >
                        {tankTypes.map((type) => {
                          const IconComponent = type.iconComponent;
                          return (
                            <MenuItem key={type.value} value={type.value}>
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <IconComponent fontSize="small" sx={{ mr: 1 }} />
                                {type.label}
                              </Box>
                            </MenuItem>
                          );
                        })}
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>

                {/* Design Parameters */}
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2, mb: 1 }}>
                  <SettingsIcon fontSize="small" sx={{ mr: 0.5, color: 'primary.main' }} />
                  <Typography variant="subtitle2" color="primary">
                    Thông số thiết kế
                  </Typography>
                </Box>

                <TextField
                  fullWidth
                  label="Lưu lượng thiết kế (m³/ngày)"
                  name="flow_rate"
                  type="number"
                  value={formData.flow_rate}
                  onChange={handleChange}
                  margin="dense"
                  size="small"
                  required
                  InputProps={{
                    endAdornment: (
                      <Tooltip title="Tổng lưu lượng nước cần xử lý trong 1 ngày">
                        <InfoIcon fontSize="small" color="action" />
                      </Tooltip>
                    ),
                  }}
                />

                {/* Detention Time with Slider */}
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    Thời gian lưu: <strong>{formData.detention_time} giờ</strong>
                    <Tooltip title={getGuide('detention_time').desc}>
                      <InfoIcon fontSize="small" color="action" sx={{ ml: 1 }} />
                    </Tooltip>
                  </Typography>
                  <Slider
                    value={formData.detention_time}
                    onChange={handleSliderChange('detention_time')}
                    min={getGuide('detention_time').min || 0.5}
                    max={getGuide('detention_time').max || 24}
                    step={0.5}
                    marks={[
                      { value: getGuide('detention_time').min || 0.5, label: `${getGuide('detention_time').min || 0.5}h` },
                      { value: getGuide('detention_time').max || 24, label: `${getGuide('detention_time').max || 24}h` },
                    ]}
                    valueLabelDisplay="auto"
                  />
                </Box>

                {/* Surface Loading Rate */}
                {formData.tank_type !== 'storage' && (
                  <TextField
                    fullWidth
                    label={`Tải trọng bề mặt (${getGuide('surface_loading_rate').unit || 'm³/m²/ngày'})`}
                    name="surface_loading_rate"
                    type="number"
                    value={formData.surface_loading_rate}
                    onChange={handleChange}
                    margin="dense"
                    size="small"
                    helperText={`Khuyến nghị: ${getGuide('surface_loading_rate').min || 20} - ${getGuide('surface_loading_rate').max || 40}`}
                  />
                )}

                {/* Depth with Slider */}
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    Chiều sâu nước: <strong>{formData.depth} m</strong>
                  </Typography>
                  <Slider
                    value={formData.depth}
                    onChange={handleSliderChange('depth')}
                    min={getGuide('depth').min || 1}
                    max={getGuide('depth').max || 6}
                    step={0.5}
                    marks={[
                      { value: getGuide('depth').min || 1, label: `${getGuide('depth').min || 1}m` },
                      { value: getGuide('depth').max || 6, label: `${getGuide('depth').max || 6}m` },
                    ]}
                    valueLabelDisplay="auto"
                  />
                </Box>

                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Số bể"
                      name="number_of_tanks"
                      type="number"
                      value={formData.number_of_tanks}
                      onChange={handleChange}
                      margin="dense"
                      size="small"
                      inputProps={{ min: 1, max: 8 }}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Tỷ lệ L/W"
                      name="length_width_ratio"
                      type="number"
                      value={formData.length_width_ratio}
                      onChange={handleChange}
                      margin="dense"
                      size="small"
                      inputProps={{ step: 0.5, min: 1.5, max: 5 }}
                    />
                  </Grid>
                </Grid>

                {/* Advanced Options */}
                <Box sx={{ mt: 2 }}>
                  <Button
                    size="small"
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    endIcon={showAdvanced ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  >
                    Tùy chọn nâng cao
                  </Button>
                  <Collapse in={showAdvanced}>
                    <Box sx={{ mt: 1, p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <TextField
                            fullWidth
                            label="Dày thành (m)"
                            name="wall_thickness"
                            type="number"
                            value={formData.wall_thickness}
                            onChange={handleChange}
                            margin="dense"
                            size="small"
                            inputProps={{ step: 0.05, min: 0.15, max: 0.5 }}
                          />
                        </Grid>
                        <Grid item xs={6}>
                          <TextField
                            fullWidth
                            label="Dày đáy (m)"
                            name="bottom_thickness"
                            type="number"
                            value={formData.bottom_thickness}
                            onChange={handleChange}
                            margin="dense"
                            size="small"
                            inputProps={{ step: 0.05, min: 0.2, max: 0.5 }}
                          />
                        </Grid>
                      </Grid>
                    </Box>
                  </Collapse>
                </Box>

                {/* Action Buttons */}
                <Box sx={{ mt: 3, display: 'flex', gap: 1 }}>
                  <Button
                    variant="outlined"
                    onClick={handleQuickCalc}
                    disabled={calculating || loading}
                    startIcon={calculating ? <CircularProgress size={18} /> : <RefreshIcon />}
                  >
                    Tính nhanh
                  </Button>
                  <Button
                    type="submit"
                    variant="contained"
                    fullWidth
                    disabled={loading}
                    startIcon={loading ? <CircularProgress size={20} /> : <CalculateIcon />}
                  >
                    {loading ? 'Đang thiết kế...' : 'Thiết kế & Xuất bản vẽ'}
                  </Button>
                </Box>
              </Box>
              )}

              {activeTab === 1 && result && (
                <Box>
                  <Alert severity={result.status === 'completed' ? 'success' : 'warning'} sx={{ mb: 2 }}>
                    {result.status === 'completed' ? 'Thiết kế hoàn thành' : 'Có cảnh báo'}
                    {' • '} Job ID: {result.job_id}
                  </Alert>

                  {/* Dimensions */}
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <StraightenIcon fontSize="small" sx={{ mr: 0.5, color: 'primary.main' }} />
                    <Typography variant="subtitle2">Kích thước bể</Typography>
                  </Box>
                  <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell>Chiều dài (L)</TableCell>
                          <TableCell align="right"><strong>{result.dimensions?.length} m</strong></TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Chiều rộng (W)</TableCell>
                          <TableCell align="right"><strong>{result.dimensions?.width} m</strong></TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Chiều sâu nước</TableCell>
                          <TableCell align="right">{result.dimensions?.depth} m</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Tổng chiều sâu</TableCell>
                          <TableCell align="right">{result.dimensions?.total_depth} m</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Số bể</TableCell>
                          <TableCell align="right">{result.dimensions?.number_of_tanks}</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>

                  {/* Hydraulic Results */}
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <WaterDropIcon fontSize="small" sx={{ mr: 0.5, color: 'info.main' }} />
                    <Typography variant="subtitle2">Kết quả thủy lực</Typography>
                  </Box>
                  <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell>Thể tích tổng</TableCell>
                          <TableCell align="right">{result.hydraulic_results?.volume?.total?.toFixed(1)} m³</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Thể tích mỗi bể</TableCell>
                          <TableCell align="right">{result.hydraulic_results?.volume?.per_tank?.toFixed(1)} m³</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Thời gian lưu</TableCell>
                          <TableCell align="right">{result.hydraulic_results?.retention_time} giờ</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Tải trọng bề mặt</TableCell>
                          <TableCell align="right">{result.hydraulic_results?.surface_loading} m³/m²/ngày</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>

                  {/* Quantities */}
                  {result.quantities && (
                    <>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <CalculateIcon fontSize="small" sx={{ mr: 0.5, color: 'secondary.main' }} />
                        <Typography variant="subtitle2">Khối lượng</Typography>
                      </Box>
                      <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                        <Table size="small">
                          <TableBody>
                            <TableRow>
                              <TableCell>Bê tông</TableCell>
                              <TableCell align="right">{result.quantities?.concrete?.toFixed(1)} m³</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Thép</TableCell>
                              <TableCell align="right">{result.quantities?.reinforcement?.toFixed(0)} kg</TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </>
                  )}

                  {/* Warnings */}
                  {result.warnings?.length > 0 && (
                    <Alert severity="warning" sx={{ mb: 2 }}>
                      <Typography variant="subtitle2">Cảnh báo:</Typography>
                      <ul style={{ margin: 0, paddingLeft: 20 }}>
                        {result.warnings.map((w, i) => (
                          <li key={i}>{typeof w === 'object' ? JSON.stringify(w) : w}</li>
                        ))}
                      </ul>
                    </Alert>
                  )}

                  {/* Download Button */}
                  {result.job_id && (
                    <Button
                      variant="contained"
                      color="success"
                      startIcon={<DownloadIcon />}
                      fullWidth
                      href={`${API_URL}/api/v1/export/download/${result.job_id}`}
                      target="_blank"
                      sx={{ mt: 2 }}
                    >
                      Tải bản vẽ DXF
                    </Button>
                  )}
                </Box>
              )}

              {activeTab === 2 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>📜 Thiết kế gần đây</Typography>
                  {recentDesigns.length === 0 ? (
                    <Alert severity="info">Chưa có thiết kế nào</Alert>
                  ) : (
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Tên</TableCell>
                            <TableCell>Loại</TableCell>
                            <TableCell>Kích thước</TableCell>
                            <TableCell>Ngày</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {recentDesigns.map((d) => (
                            <TableRow key={d.id} hover>
                              <TableCell>{d.name}</TableCell>
                              <TableCell>{d.type}</TableCell>
                              <TableCell>{d.dimensions?.length}x{d.dimensions?.width}m</TableCell>
                              <TableCell>{new Date(d.date).toLocaleDateString('vi-VN')}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Right Panel - Preview */}
        <Grid item xs={12} md={7}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Live Preview */}
          <DXFPreview
            dimensions={result?.dimensions || previewDimensions}
            type="tank"
            title={`Preview: ${formData.tank_name || 'Bể mới'}`}
            downloadUrl={
              result?.drawing_file
                ? `${API_URL}/api/v1/export/download/${result.job_id}/${result.drawing_file.split('/').pop()}`
                : null
            }
          />

          {/* Quick Info Cards */}
          {previewDimensions && (
            <Grid container spacing={2} sx={{ mt: 2 }}>
              <Grid item xs={4}>
                <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light', color: 'white' }}>
                  <Typography variant="h6">{previewDimensions.volume} m³</Typography>
                  <Typography variant="body2">Thể tích/bể</Typography>
                </Paper>
              </Grid>
              <Grid item xs={4}>
                <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'white' }}>
                  <Typography variant="h6">{previewDimensions.surface_area} m²</Typography>
                  <Typography variant="body2">Diện tích</Typography>
                </Paper>
              </Grid>
              <Grid item xs={4}>
                <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light', color: 'white' }}>
                  <Typography variant="h6">{previewDimensions.length}x{previewDimensions.width}</Typography>
                  <Typography variant="body2">L x W (m)</Typography>
                </Paper>
              </Grid>
            </Grid>
          )}

          {/* Design Tips */}
          <Paper sx={{ p: 2, mt: 2, bgcolor: 'grey.50' }}>
            <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}><TipsAndUpdatesIcon fontSize="small" sx={{ mr: 1 }} /> Gợi ý thiết kế - {tankTypes.find(t => t.value === formData.tank_type)?.label}</Typography>
            <Typography variant="body2" color="text.secondary">
              {formData.tank_type === 'sedimentation' && (
                <>
                  • Tỷ lệ L/W = 3-5 để đảm bảo dòng chảy đều<br />
                  • Vận tốc ngang &lt; 0.01 m/s<br />
                  • Tải trọng bề mặt 20-40 m³/m²/ngày (TCVN 7957)
                </>
              )}
              {formData.tank_type === 'storage' && (
                <>
                  • Dự trữ 4-12 giờ lưu lượng<br />
                  • Chiều cao an toàn tối thiểu 0.3m<br />
                  • Bố trí 2 bể để vận hành xen kẽ
                </>
              )}
              {formData.tank_type === 'buffer' && (
                <>
                  • Thời gian điều hòa 4-8 giờ<br />
                  • Lắp đặt thiết bị khuấy trộn<br />
                  • Đảm bảo đầu ra ổn định lưu lượng
                </>
              )}
              {formData.tank_type === 'filtration' && (
                <>
                  • Tải trọng lọc 5-12 m³/m²/h<br />
                  • Chiều dày lớp cát 0.6-0.8m<br />
                  • Chu kỳ rửa lọc 24-48 giờ
                </>
              )}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Progress Dialog */}
      <Dialog 
        open={progressOpen} 
        maxWidth="sm" 
        fullWidth
        PaperProps={{
          sx: { borderRadius: 2 }
        }}
      >
        <DialogTitle sx={{ bgcolor: 'primary.main', color: 'white', py: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <EngineeringIcon sx={{ mr: 1 }} />
            <Typography variant="h6">Đang thiết kế...</Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <LinearProgress 
            variant="determinate" 
            value={(progressStep + 1) / progressSteps.length * 100} 
            sx={{ mb: 3, height: 8, borderRadius: 4 }}
          />
          
          <Stepper activeStep={progressStep} orientation="vertical">
            {progressSteps.map((step, index) => (
              <Step key={index} completed={step.status === 'completed'}>
                <StepLabel
                  StepIconProps={{
                    icon: step.status === 'completed' 
                      ? <CheckCircleIcon color="success" />
                      : step.status === 'active' 
                        ? <CircularProgress size={24} />
                        : <PendingIcon color="disabled" />
                  }}
                >
                  <Typography 
                    variant="subtitle2" 
                    color={step.status === 'active' ? 'primary' : 'inherit'}
                    fontWeight={step.status === 'active' ? 600 : 400}
                  >
                    {step.label}
                  </Typography>
                </StepLabel>
                <StepContent>
                  {step.formula && (
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontFamily: 'monospace', bgcolor: 'grey.100', p: 0.5, borderRadius: 1, mb: 0.5 }}>
                      <FunctionsIcon sx={{ fontSize: 14, verticalAlign: 'middle', mr: 0.5 }} />
                      {step.formula}
                    </Typography>
                  )}
                  {step.detail && (
                    <Typography variant="body2" color={step.status === 'completed' ? 'success.main' : 'text.secondary'}>
                      {step.detail}
                    </Typography>
                  )}
                </StepContent>
              </Step>
            ))}
          </Stepper>
          
          {progressStep >= progressSteps.length - 1 && progressSteps.every(s => s.status === 'completed') && (
            <Alert severity="success" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Thiết kế hoàn thành!</strong> Đang chuyển sang kết quả...
              </Typography>
            </Alert>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
}

export default TankDesignPage;
