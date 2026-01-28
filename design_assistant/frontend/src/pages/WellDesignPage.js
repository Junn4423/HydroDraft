import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
  TableRow,
  Tabs,
  Tab,
  Chip,
  Slider,
  Tooltip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Calculate as CalculateIcon,
  Download as DownloadIcon,
  Info as InfoIcon,
  CheckCircle as CheckIcon,
  Opacity as WellIcon,
  Assessment as MonitoringIcon,
  Power as PumpingIcon,
  Search as ObservationIcon,
  Inventory as MaterialIcon,
  Build as ConstructionIcon,
  History as HistoryIcon,
  TipsAndUpdates as TipsAndUpdatesIcon,
} from '@mui/icons-material';
import axios from 'axios';
import DXFPreview from '../components/DXFPreview';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const wellTypes = [
  { value: 'monitoring', label: 'Giếng quan trắc', iconComponent: MonitoringIcon },
  { value: 'pumping', label: 'Giếng bơm', iconComponent: PumpingIcon },
  { value: 'observation', label: 'Giếng khảo sát', iconComponent: ObservationIcon },
];

const casingMaterials = [
  { value: 'PVC', label: 'PVC-U', maxDepth: 100, color: '#1976d2' },
  { value: 'HDPE', label: 'HDPE', maxDepth: 150, color: '#388e3c' },
  { value: 'Stainless_steel', label: 'Thép không gỉ', maxDepth: 300, color: '#7b1fa2' },
];

const standardDiameters = [50, 60, 75, 90, 110, 125, 160, 200];

function WellDesignPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [formData, setFormData] = useState({
    project_name: '',
    well_name: '',
    well_type: 'monitoring',
    x_coordinate: 0,
    y_coordinate: 0,
    ground_level: 10.0,
    total_depth: 30,
    casing_diameter: 110,
    casing_material: 'PVC',
    screen_top: null,
    screen_bottom: null,
    screen_slot_size: 0.5,
    geology: null,
    generate_drawing: true,
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [recentDesigns, setRecentDesigns] = useState([]);

  // Auto-calculate screen positions
  useEffect(() => {
    if (!formData.screen_top) {
      setFormData(prev => ({
        ...prev,
        screen_top: Math.round(prev.total_depth * 0.6),
        screen_bottom: prev.total_depth,
      }));
    }
  }, [formData.total_depth]);

  // Load recent designs
  useEffect(() => {
    const saved = localStorage.getItem('recentWellDesigns');
    if (saved) {
      setRecentDesigns(JSON.parse(saved));
    }
  }, []);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    let newValue = value;
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

    try {
      const response = await axios.post(
        `${API_URL}/api/v1/design/well/?_t=${Date.now()}`,
        formData,
        {
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
          },
        }
      );
      setResult(response.data);

      // Save to recent designs
      const newDesign = {
        id: response.data.job_id,
        name: formData.well_name,
        type: formData.well_type,
        depth: formData.total_depth,
        date: new Date().toISOString(),
      };
      const updated = [newDesign, ...recentDesigns.slice(0, 9)];
      setRecentDesigns(updated);
      localStorage.setItem('recentWellDesigns', JSON.stringify(updated));

      setActiveTab(1);
    } catch (err) {
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

  const getScreenLength = useCallback(() => {
    const top = formData.screen_top || formData.total_depth * 0.6;
    const bottom = formData.screen_bottom || formData.total_depth;
    return Math.round((bottom - top) * 10) / 10;
  }, [formData.screen_top, formData.screen_bottom, formData.total_depth]);

  const getScreenRatio = useCallback(() => {
    const screenLength = getScreenLength();
    return Math.round((screenLength / formData.total_depth) * 100);
  }, [formData.total_depth, getScreenLength]);

  // Preview data that updates in real-time
  const previewDimensions = useMemo(() => ({
    depth: formData.total_depth,
    diameter: formData.casing_diameter,
    screen_length: getScreenLength(),
    screen_ratio: getScreenRatio(),
    material: formData.casing_material,
  }), [formData.total_depth, formData.casing_diameter, formData.casing_material, getScreenLength, getScreenRatio]);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">💧 Thiết kế Giếng quan trắc</Typography>
        <Chip
          label={wellTypes.find((t) => t.value === formData.well_type)?.label}
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
                    <WellIcon fontSize="small" sx={{ mr: 0.5, color: 'primary.main' }} />
                    <Typography variant="subtitle2" color="primary">Thông tin cơ bản</Typography>
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
                        label="Ký hiệu giếng"
                        name="well_name"
                        value={formData.well_name}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                        required
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <FormControl fullWidth margin="dense" size="small">
                        <InputLabel>Loại giếng</InputLabel>
                        <Select
                          name="well_type"
                          value={formData.well_type}
                          label="Loại giếng"
                          onChange={handleChange}
                        >
                          {wellTypes.map((type) => (
                            <MenuItem key={type.value} value={type.value}>
                              {type.icon} {type.label}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                  </Grid>

                  {/* Location */}
                  <Typography variant="subtitle2" color="primary" sx={{ mt: 2 }} gutterBottom>
                    📍 Vị trí
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        label="Tọa độ X"
                        name="x_coordinate"
                        type="number"
                        value={formData.x_coordinate}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        label="Tọa độ Y"
                        name="y_coordinate"
                        type="number"
                        value={formData.y_coordinate}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        label="Cao độ MĐ (m)"
                        name="ground_level"
                        type="number"
                        value={formData.ground_level}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                        inputProps={{ step: 0.1 }}
                      />
                    </Grid>
                  </Grid>

                  {/* Design Parameters */}
                  <Typography variant="subtitle2" color="primary" sx={{ mt: 2 }} gutterBottom>
                    ⚙️ Thông số thiết kế
                  </Typography>

                  {/* Total Depth Slider */}
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="body2" gutterBottom>
                      Tổng chiều sâu: <strong>{formData.total_depth} m</strong>
                    </Typography>
                    <Slider
                      value={formData.total_depth}
                      onChange={handleSliderChange('total_depth')}
                      min={5}
                      max={150}
                      step={5}
                      marks={[
                        { value: 5, label: '5m' },
                        { value: 50, label: '50m' },
                        { value: 100, label: '100m' },
                        { value: 150, label: '150m' },
                      ]}
                      valueLabelDisplay="auto"
                    />
                  </Box>

                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <FormControl fullWidth margin="dense" size="small">
                        <InputLabel>Đường kính ống (mm)</InputLabel>
                        <Select
                          name="casing_diameter"
                          value={formData.casing_diameter}
                          label="Đường kính ống (mm)"
                          onChange={handleChange}
                        >
                          {standardDiameters.map((d) => (
                            <MenuItem key={d} value={d}>
                              Ø{d} mm
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={6}>
                      <FormControl fullWidth margin="dense" size="small">
                        <InputLabel>Vật liệu ống</InputLabel>
                        <Select
                          name="casing_material"
                          value={formData.casing_material}
                          label="Vật liệu ống"
                          onChange={handleChange}
                        >
                          {casingMaterials.map((mat) => (
                            <MenuItem key={mat.value} value={mat.value}>
                              {mat.label} (≤{mat.maxDepth}m)
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                  </Grid>

                  {/* Screen Settings */}
                  <Typography variant="subtitle2" color="primary" sx={{ mt: 2 }} gutterBottom>
                    🔩 Ống lọc (Screen)
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        label="Đỉnh (m)"
                        name="screen_top"
                        type="number"
                        value={formData.screen_top || Math.round(formData.total_depth * 0.6)}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                        inputProps={{ min: 0, max: formData.total_depth }}
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        label="Đáy (m)"
                        name="screen_bottom"
                        type="number"
                        value={formData.screen_bottom || formData.total_depth}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                        inputProps={{ min: 0, max: formData.total_depth }}
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        label="Khe (mm)"
                        name="screen_slot_size"
                        type="number"
                        value={formData.screen_slot_size}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                        inputProps={{ step: 0.1, min: 0.3, max: 2 }}
                      />
                    </Grid>
                  </Grid>

                  {/* Quick Stats */}
                  <Box sx={{ mt: 2, p: 1.5, bgcolor: 'grey.100', borderRadius: 1 }}>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">Chiều dài ống lọc</Typography>
                        <Typography variant="body1" fontWeight="bold">{getScreenLength()} m ({getScreenRatio()}%)</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">ĐK lỗ khoan</Typography>
                        <Typography variant="body1" fontWeight="bold">{formData.casing_diameter + 100} mm</Typography>
                      </Grid>
                    </Grid>
                  </Box>

                  {/* Material Warning */}
                  {formData.total_depth > casingMaterials.find(m => m.value === formData.casing_material)?.maxDepth && (
                    <Alert severity="warning" sx={{ mt: 2 }}>
                      Vật liệu {formData.casing_material} không khuyến nghị cho giếng sâu >{casingMaterials.find(m => m.value === formData.casing_material)?.maxDepth}m
                    </Alert>
                  )}

                  {/* Submit Button */}
                  <Button
                    type="submit"
                    variant="contained"
                    fullWidth
                    disabled={loading}
                    startIcon={loading ? <CircularProgress size={20} /> : <CalculateIcon />}
                    sx={{ mt: 2 }}
                  >
                    {loading ? 'Đang thiết kế...' : 'Thiết kế giếng'}
                  </Button>
                </Box>
              )}

              {activeTab === 1 && result && (
                <Box>
                  <Alert severity={result.status === 'completed' ? 'success' : 'warning'} sx={{ mb: 2 }}>
                    {result.status === 'completed' ? '✅ Thiết kế hoàn thành' : '⚠️ Có cảnh báo'}
                    {' • '} Job ID: {result.job_id}
                  </Alert>

                  {/* Design Summary */}
                  <Typography variant="subtitle2" gutterBottom>📐 Thông số thiết kế</Typography>
                  <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell>Tổng chiều sâu</TableCell>
                          <TableCell align="right"><strong>{result.design?.total_depth} m</strong></TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>ĐK ống chống</TableCell>
                          <TableCell align="right">{result.design?.casing_diameter} mm</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>ĐK lỗ khoan</TableCell>
                          <TableCell align="right">{result.design?.borehole_diameter} mm</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Chiều dài ống lọc</TableCell>
                          <TableCell align="right">{result.design?.screen_length} m</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>

                  {/* Materials */}
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <MaterialIcon fontSize="small" sx={{ mr: 0.5, color: 'primary.main' }} />
                    <Typography variant="subtitle2">Vật liệu</Typography>
                  </Box>
                  <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell>Ống chống</TableCell>
                          <TableCell align="right">{result.materials?.casing?.length} m</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Ống lọc</TableCell>
                          <TableCell align="right">{result.materials?.screen?.length} m</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Sỏi lọc</TableCell>
                          <TableCell align="right">{result.materials?.gravel?.volume} m³</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Bentonite</TableCell>
                          <TableCell align="right">{result.materials?.bentonite?.quantity} kg</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Xi măng</TableCell>
                          <TableCell align="right">{result.materials?.cement?.quantity} kg</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>

                  {/* Construction Steps */}
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <ConstructionIcon fontSize="small" sx={{ mr: 0.5, color: 'secondary.main' }} />
                    <Typography variant="subtitle2">Quy trình thi công</Typography>
                  </Box>
                  <List dense>
                    {result.construction_steps?.map((step, i) => (
                      <ListItem key={i} sx={{ py: 0 }}>
                        <ListItemIcon sx={{ minWidth: 30 }}>
                          <CheckIcon fontSize="small" color="success" />
                        </ListItemIcon>
                        <ListItemText primary={step} primaryTypographyProps={{ variant: 'body2' }} />
                      </ListItem>
                    ))}
                  </List>

                  {/* Validation Warnings */}
                  {result.validation?.warnings?.length > 0 && (
                    <Alert severity="warning" sx={{ mt: 2 }}>
                      <Typography variant="subtitle2">Cảnh báo:</Typography>
                      <ul style={{ margin: 0, paddingLeft: 20 }}>
                        {result.validation.warnings.map((w, i) => (
                          <li key={i}>{w}</li>
                        ))}
                      </ul>
                    </Alert>
                  )}

                  {/* Download Button */}
                  {result.drawing_file && (
                    <Button
                      variant="contained"
                      startIcon={<DownloadIcon />}
                      fullWidth
                      sx={{ mt: 2 }}
                      href={`${API_URL}/api/v1/export/download/${result.job_id}/${result.drawing_file.split('/').pop()}`}
                    >
                      Tải bản vẽ DXF
                    </Button>
                  )}
                </Box>
              )}

              {activeTab === 2 && (
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <HistoryIcon fontSize="small" sx={{ mr: 0.5, color: 'primary.main' }} />
                    <Typography variant="subtitle2">Thiết kế gần đây</Typography>
                  </Box>
                  {recentDesigns.length === 0 ? (
                    <Alert severity="info">Chưa có thiết kế nào</Alert>
                  ) : (
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableBody>
                          {recentDesigns.map((d) => (
                            <TableRow key={d.id} hover>
                              <TableCell>{d.name}</TableCell>
                              <TableCell>{d.depth}m</TableCell>
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
            type="well"
            title={`Preview: ${formData.well_name || 'Giếng mới'}`}
            drawingData={result || {
              design: {
                total_depth: formData.total_depth,
                casing_diameter: formData.casing_diameter,
                borehole_diameter: formData.casing_diameter + 100,
              },
              structure: {
                screen: {
                  depth_from: formData.screen_top || formData.total_depth * 0.6,
                  depth_to: formData.screen_bottom || formData.total_depth,
                },
              },
            }}
            downloadUrl={
              result?.drawing_file
                ? `${API_URL}/api/v1/export/download/${result.job_id}/${result.drawing_file.split('/').pop()}`
                : null
            }
          />

          {/* Quick Info Cards */}
          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={4}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light', color: 'white' }}>
                <Typography variant="h6">{formData.total_depth} m</Typography>
                <Typography variant="body2">Chiều sâu</Typography>
              </Paper>
            </Grid>
            <Grid item xs={4}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'white' }}>
                <Typography variant="h6">Ø{formData.casing_diameter}</Typography>
                <Typography variant="body2">Đường kính</Typography>
              </Paper>
            </Grid>
            <Grid item xs={4}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light', color: 'white' }}>
                <Typography variant="h6">{getScreenLength()} m</Typography>
                <Typography variant="body2">Ống lọc</Typography>
              </Paper>
            </Grid>
          </Grid>

          {/* Design Tips */}
          <Paper sx={{ p: 2, mt: 2, bgcolor: 'grey.50' }}>
            <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}><TipsAndUpdatesIcon fontSize="small" sx={{ mr: 1 }} /> Gợi ý thiết kế</Typography>
            <Typography variant="body2" color="text.secondary">
              • Tỷ lệ ống lọc: 20-50% chiều sâu giếng<br />
              • Kích thước sỏi lọc: 4-6 lần khe ống lọc<br />
              • Chiều dày nút bentonite: 0.5-1m<br />
              • Ống bảo vệ cao hơn mặt đất 0.3-0.5m<br />
              • Theo TCVN 9901:2014 - Giếng khoan nước
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default WellDesignPage;
