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
  IconButton,
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
  Tooltip,
} from '@mui/material';
import { 
  Add as AddIcon, 
  Delete as DeleteIcon, 
  Calculate as CalculateIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Timeline as TimelineIcon,
  ArrowDownward as GravityIcon,
  Air as PressureIcon,
  Water as WastewaterIcon,
  WaterDrop as StormwaterIcon,
  Opacity as WaterSupplyIcon,
  Assignment as AssignmentIcon,
  BarChart as BarChartIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  TipsAndUpdates as TipsAndUpdatesIcon,
} from '@mui/icons-material';
import axios from 'axios';
import DXFPreview from '../components/DXFPreview';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const pipeTypes = [
  { value: 'gravity', label: 'Ống tự chảy', iconComponent: GravityIcon },
  { value: 'pressure', label: 'Ống có áp', iconComponent: PressureIcon },
];

const flowTypes = [
  { value: 'wastewater', label: 'Nước thải', iconComponent: WastewaterIcon },
  { value: 'stormwater', label: 'Nước mưa', iconComponent: StormwaterIcon },
  { value: 'water_supply', label: 'Cấp nước', iconComponent: WaterSupplyIcon },
];

const materials = [
  { value: 'concrete', label: 'Bê tông cốt thép', roughness: 0.013 },
  { value: 'hdpe', label: 'HDPE', roughness: 0.010 },
  { value: 'pvc', label: 'PVC-U', roughness: 0.010 },
  { value: 'composite', label: 'Composite (GRP)', roughness: 0.011 },
  { value: 'ductile_iron', label: 'Gang dẻo', roughness: 0.012 },
];

function PipelineDesignPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [formData, setFormData] = useState({
    project_name: '',
    pipeline_name: '',
    pipe_type: 'gravity',
    flow_type: 'wastewater',
    design_flow: 100,
    material: 'concrete',
    min_cover_depth: 0.7,
    manholes: [
      { station: 0, ground_level: 10.0, name: 'MH1' },
      { station: 50, ground_level: 9.8, name: 'MH2' },
      { station: 100, ground_level: 9.5, name: 'MH3' },
    ],
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [recentDesigns, setRecentDesigns] = useState([]);

  // Load recent designs
  useEffect(() => {
    const saved = localStorage.getItem('recentPipelineDesigns');
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

  const handleManholeChange = (index, field, value) => {
    const newManholes = [...formData.manholes];
    newManholes[index] = {
      ...newManholes[index],
      [field]: field === 'name' ? value : parseFloat(value) || 0,
    };
    setFormData((prev) => ({
      ...prev,
      manholes: newManholes,
    }));
  };

  const addManhole = () => {
    const lastMh = formData.manholes[formData.manholes.length - 1];
    setFormData((prev) => ({
      ...prev,
      manholes: [
        ...prev.manholes,
        {
          station: lastMh.station + 50,
          ground_level: lastMh.ground_level - 0.2,
          name: `MH${prev.manholes.length + 1}`,
        },
      ],
    }));
  };

  const removeManhole = (index) => {
    if (formData.manholes.length > 2) {
      setFormData((prev) => ({
        ...prev,
        manholes: prev.manholes.filter((_, i) => i !== index),
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        `${API_URL}/api/v1/design/pipeline/?_t=${Date.now()}`,
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
        name: formData.pipeline_name,
        type: formData.pipe_type,
        flow_type: formData.flow_type,
        total_length: response.data.total_length,
        date: new Date().toISOString(),
      };
      const updated = [newDesign, ...recentDesigns.slice(0, 9)];
      setRecentDesigns(updated);
      localStorage.setItem('recentPipelineDesigns', JSON.stringify(updated));

      setActiveTab(1);
    } catch (err) {
      const errorDetail = err.response?.data?.detail;
      if (Array.isArray(errorDetail)) {
        const messages = errorDetail.map(e => 
          typeof e === 'object' ? (e.msg || e.message || JSON.stringify(e)) : e
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

  // Calculate total length and slope for preview - now using useMemo for real-time updates
  const getTotalLength = useCallback(() => {
    if (formData.manholes.length < 2) return 0;
    return formData.manholes[formData.manholes.length - 1].station - formData.manholes[0].station;
  }, [formData.manholes]);

  const getAverageSlope = useCallback(() => {
    if (formData.manholes.length < 2) return 0;
    const first = formData.manholes[0];
    const last = formData.manholes[formData.manholes.length - 1];
    const length = last.station - first.station;
    if (length === 0) return 0;
    const drop = first.ground_level - last.ground_level;
    return ((drop / length) * 1000).toFixed(1); // ‰
  }, [formData.manholes]);

  // Preview data that updates in real-time
  const previewData = useMemo(() => {
    const totalLength = getTotalLength();
    const avgSlope = getAverageSlope();
    return {
      totalLength,
      avgSlope,
      numManholes: formData.manholes.length,
      segments: formData.manholes.slice(0, -1).map((mh, i) => ({
        id: i + 1,
        from: mh.name,
        to: formData.manholes[i + 1].name,
        length: formData.manholes[i + 1].station - mh.station,
        slope: ((mh.ground_level - formData.manholes[i + 1].ground_level) / 
               (formData.manholes[i + 1].station - mh.station) * 1000).toFixed(1),
      })),
    };
  }, [formData.manholes, getTotalLength, getAverageSlope]);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <TimelineIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h5">Thiết kế Đường ống</Typography>
        </Box>
        <Box>
          <Chip
            label={pipeTypes.find((t) => t.value === formData.pipe_type)?.label}
            color="primary"
            variant="outlined"
            sx={{ mr: 1 }}
          />
          <Chip
            label={flowTypes.find((t) => t.value === formData.flow_type)?.label}
            color="secondary"
            variant="outlined"
          />
        </Box>
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
                      label="Ký hiệu tuyến"
                      name="pipeline_name"
                      value={formData.pipeline_name}
                      onChange={handleChange}
                      margin="dense"
                      size="small"
                      required
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <FormControl fullWidth margin="dense" size="small">
                      <InputLabel>Loại ống</InputLabel>
                      <Select
                        name="pipe_type"
                        value={formData.pipe_type}
                        label="Loại ống"
                        onChange={handleChange}
                      >
                        {pipeTypes.map((type) => (
                          <MenuItem key={type.value} value={type.value}>
                            {type.icon} {type.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>

                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <FormControl fullWidth margin="dense" size="small">
                      <InputLabel>Loại dòng chảy</InputLabel>
                      <Select
                        name="flow_type"
                        value={formData.flow_type}
                        label="Loại dòng chảy"
                        onChange={handleChange}
                      >
                        {flowTypes.map((type) => (
                          <MenuItem key={type.value} value={type.value}>
                            {type.icon} {type.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={6}>
                    <FormControl fullWidth margin="dense" size="small">
                      <InputLabel>Vật liệu</InputLabel>
                      <Select
                        name="material"
                        value={formData.material}
                        label="Vật liệu"
                        onChange={handleChange}
                      >
                        {materials.map((mat) => (
                          <MenuItem key={mat.value} value={mat.value}>
                            {mat.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>

                <Typography variant="subtitle2" color="primary" sx={{ mt: 2 }} gutterBottom>
                  ⚙️ Thông số thiết kế
                </Typography>

                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Lưu lượng (L/s)"
                      name="design_flow"
                      type="number"
                      value={formData.design_flow}
                      onChange={handleChange}
                      margin="dense"
                      size="small"
                      required
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Độ sâu chôn min (m)"
                      name="min_cover_depth"
                      type="number"
                      value={formData.min_cover_depth}
                      onChange={handleChange}
                      margin="dense"
                      size="small"
                      inputProps={{ step: 0.1, min: 0.3, max: 3 }}
                    />
                  </Grid>
                </Grid>

                {/* Manholes Table */}
                <Typography variant="subtitle2" color="primary" sx={{ mt: 2 }} gutterBottom>
                  📍 Danh sách giếng thăm
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Tên</TableCell>
                        <TableCell>Lý trình (m)</TableCell>
                        <TableCell>Cao độ MĐ (m)</TableCell>
                        <TableCell width={40}></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {formData.manholes.map((mh, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <TextField
                              size="small"
                              value={mh.name}
                              onChange={(e) => handleManholeChange(index, 'name', e.target.value)}
                              variant="standard"
                              sx={{ width: 60 }}
                            />
                          </TableCell>
                          <TableCell>
                            <TextField
                              size="small"
                              type="number"
                              value={mh.station}
                              onChange={(e) => handleManholeChange(index, 'station', e.target.value)}
                              variant="standard"
                              sx={{ width: 70 }}
                            />
                          </TableCell>
                          <TableCell>
                            <TextField
                              size="small"
                              type="number"
                              value={mh.ground_level}
                              onChange={(e) => handleManholeChange(index, 'ground_level', e.target.value)}
                              variant="standard"
                              inputProps={{ step: 0.1 }}
                              sx={{ width: 70 }}
                            />
                          </TableCell>
                          <TableCell>
                            <IconButton
                              size="small"
                              onClick={() => removeManhole(index)}
                              disabled={formData.manholes.length <= 2}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                <Button
                  startIcon={<AddIcon />}
                  onClick={addManhole}
                  size="small"
                  sx={{ mt: 1 }}
                >
                  Thêm giếng
                </Button>

                {/* Quick Stats */}
                <Box sx={{ mt: 2, p: 1.5, bgcolor: 'grey.100', borderRadius: 1 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Tổng chiều dài</Typography>
                      <Typography variant="body1" fontWeight="bold">{previewData.totalLength} m</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Độ dốc TB</Typography>
                      <Typography variant="body1" fontWeight="bold">{previewData.avgSlope} ‰</Typography>
                    </Grid>
                  </Grid>
                </Box>

                {/* Submit Button */}
                <Button
                  type="submit"
                  variant="contained"
                  fullWidth
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <CalculateIcon />}
                  sx={{ mt: 2 }}
                >
                  {loading ? 'Đang thiết kế...' : 'Thiết kế tuyến ống'}
                </Button>
              </Box>
              )}

              {activeTab === 1 && result && (
                <Box>
                  <Alert severity={result.status === 'completed' ? 'success' : 'warning'} sx={{ mb: 2 }}>
                    {result.status === 'completed' ? 'Thiết kế hoàn thành' : 'Có cảnh báo'}
                    {' • '}Tổng chiều dài: {result.total_length} m
                  </Alert>

                  {/* Segments Table */}
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <BarChartIcon fontSize="small" sx={{ mr: 0.5, color: 'primary.main' }} />
                    <Typography variant="subtitle2">Kết quả từng đoạn</Typography>
                  </Box>
                  <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Đoạn</TableCell>
                          <TableCell align="right">L (m)</TableCell>
                          <TableCell align="right">i (‰)</TableCell>
                          <TableCell align="right">D (mm)</TableCell>
                          <TableCell align="right">v (m/s)</TableCell>
                          <TableCell align="right">h/D</TableCell>
                          <TableCell align="center">OK</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {result.segments?.map((seg) => (
                          <TableRow key={seg.segment_id}>
                            <TableCell sx={{ fontSize: '0.75rem' }}>{seg.start_manhole}→{seg.end_manhole}</TableCell>
                            <TableCell align="right">{seg.length}</TableCell>
                            <TableCell align="right">{seg.slope}</TableCell>
                            <TableCell align="right"><strong>{seg.diameter}</strong></TableCell>
                            <TableCell align="right">{seg.velocity}</TableCell>
                            <TableCell align="right">{seg.filling_ratio}</TableCell>
                            <TableCell align="center">{seg.valid ? <CheckCircleIcon fontSize="small" color="success" /> : <WarningIcon fontSize="small" color="warning" />}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>

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

                  {/* Download */}
                  {result.drawing_file && (
                    <Button
                      variant="contained"
                      startIcon={<DownloadIcon />}
                      fullWidth
                      href={`${API_URL}/api/v1/export/download/${result.job_id}/${result.drawing_file.split('/').pop()}`}
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
                            <TableCell>Dài (m)</TableCell>
                            <TableCell>Ngày</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {recentDesigns.map((d) => (
                            <TableRow key={d.id} hover>
                              <TableCell>{d.name}</TableCell>
                              <TableCell>{d.type}</TableCell>
                              <TableCell>{d.total_length}</TableCell>
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
            type="pipeline"
            title={`Preview: ${formData.pipeline_name || 'Tuyến ống mới'}`}
            drawingData={result || {
              segments: formData.manholes.slice(0, -1).map((mh, i) => ({
                segment_id: i + 1,
                start_station: mh.station,
                end_station: formData.manholes[i + 1].station,
                ground_start: mh.ground_level,
                ground_end: formData.manholes[i + 1].ground_level,
                invert_start: mh.ground_level - formData.min_cover_depth - 0.3,
                invert_end: formData.manholes[i + 1].ground_level - formData.min_cover_depth - 0.3,
              })),
              total_length: getTotalLength(),
            }}
            downloadUrl={
              result?.drawing_file
                ? `${API_URL}/api/v1/export/download/${result.job_id}/${result.drawing_file.split('/').pop()}`
                : null
            }
          />

          {/* Quick Info */}
          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={4}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light', color: 'white' }}>
                <Typography variant="h6">{getTotalLength()} m</Typography>
                <Typography variant="body2">Tổng chiều dài</Typography>
              </Paper>
            </Grid>
            <Grid item xs={4}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'white' }}>
                <Typography variant="h6">{formData.manholes.length}</Typography>
                <Typography variant="body2">Số giếng</Typography>
              </Paper>
            </Grid>
            <Grid item xs={4}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light', color: 'white' }}>
                <Typography variant="h6">{getAverageSlope()} ‰</Typography>
                <Typography variant="body2">Độ dốc TB</Typography>
              </Paper>
            </Grid>
          </Grid>

          {/* Design Tips */}
          <Paper sx={{ p: 2, mt: 2, bgcolor: 'grey.50' }}>
            <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}><TipsAndUpdatesIcon fontSize="small" sx={{ mr: 1 }} /> Gợi ý thiết kế</Typography>
            <Typography variant="body2" color="text.secondary">
              {formData.pipe_type === 'gravity' && (
                <>
                  • Độ dốc tối thiểu: 3-5‰ cho D150-300mm<br />
                  • Vận tốc tự rửa: ≥ 0.7 m/s (TCVN 7957)<br />
                  • Tỷ lệ đầy h/D: 0.5-0.8 cho ống thoát nước thải
                </>
              )}
              {formData.pipe_type === 'pressure' && (
                <>
                  • Vận tốc kinh tế: 0.8-1.5 m/s<br />
                  • Áp suất làm việc: 6-10 bar<br />
                  • Kiểm tra búa nước khi đóng van
                </>
              )}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default PipelineDesignPage;
