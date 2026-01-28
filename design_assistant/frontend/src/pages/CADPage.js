/**
 * CAD Professional Page
 * Tạo bản vẽ CAD chuyên nghiệp (Sprint 3)
 */

import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Chip,
  Divider,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Draw as CADIcon,
  Download as DownloadIcon,
  CheckCircle as ValidIcon,
  Assignment as AssignmentIcon,
  Layers as LayersIcon,
} from '@mui/icons-material';
import { cadAPI, exportAPI } from '../services/api';
import DXFPreview from '../components/DXFPreview';
import CADValidation from '../components/CADValidation';

const CADPage = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const [formData, setFormData] = useState({
    // Project info
    project_name: '',
    drawing_title: 'MẶT BẰNG VÀ MẶT CẮT BỂ',
    drawing_number: 'TD-01',
    drawn_by: 'HydroDraft',
    scale: '1:100',
    
    // Tank dimensions
    length: 10,
    width: 5,
    water_depth: 3,
    total_depth: 4,
    wall_thickness: 0.3,
    bottom_thickness: 0.3,
    freeboard: 0.3,
    
    // Pipes
    inlet_diameter: 200,
    outlet_diameter: 200,
    
    // Reinforcement
    main_rebar_dia: 12,
    main_rebar_spacing: 200,
    dist_rebar_dia: 10,
    dist_rebar_spacing: 250,
    cover: 0.03,
    
    // Levels
    ground_level: 0.0,
    
    // Options
    include_plan: true,
    include_section: true,
    include_rebar: true,
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : (type === 'number' ? parseFloat(value) : value),
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await cadAPI.createTankDrawing(formData);
      setResult(response.data);
      setActiveTab(1);
    } catch (err) {
      setError(err.response?.data?.detail || 'Lỗi khi tạo bản vẽ');
    } finally {
      setLoading(false);
    }
  };

  const scales = ['1:25', '1:50', '1:100', '1:200', '1:500'];

  return (
    <Container maxWidth="xl">
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <CADIcon color="primary" sx={{ fontSize: 40, mr: 2 }} />
        <Box>
          <Typography variant="h4">CAD Chuyên nghiệp</Typography>
          <Typography variant="body2" color="text.secondary">
            Tạo bản vẽ kỹ thuật tiêu chuẩn TCVN với đầy đủ layers, blocks và annotations
          </Typography>
        </Box>
        <Chip label="Sprint 3" color="primary" sx={{ ml: 'auto' }} />
      </Box>

      <Grid container spacing={3}>
        {/* Left - Form */}
        <Grid item xs={12} md={5}>
          <Card>
            <CardContent>
              <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ mb: 2 }}>
                <Tab label="Nhập liệu" />
                <Tab label="Kết quả" disabled={!result} />
                <Tab label="Validation" disabled={!result} />
              </Tabs>

              {activeTab === 0 && (
                <Box component="form" onSubmit={handleSubmit}>
                  {/* Project Info */}
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <AssignmentIcon fontSize="small" sx={{ mr: 0.5, color: 'primary.main' }} />
                    <Typography variant="subtitle2" color="primary">Thông tin Bản vẽ</Typography>
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
                    <Grid item xs={8}>
                      <TextField
                        fullWidth
                        label="Tiêu đề bản vẽ"
                        name="drawing_title"
                        value={formData.drawing_title}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        label="Số bản vẽ"
                        name="drawing_number"
                        value={formData.drawing_number}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                      />
                    </Grid>
                  </Grid>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        label="Người vẽ"
                        name="drawn_by"
                        value={formData.drawn_by}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <FormControl fullWidth margin="dense" size="small">
                        <InputLabel>Tỷ lệ</InputLabel>
                        <Select
                          name="scale"
                          value={formData.scale}
                          label="Tỷ lệ"
                          onChange={handleChange}
                        >
                          {scales.map(s => (
                            <MenuItem key={s} value={s}>{s}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                  </Grid>

                  <Divider sx={{ my: 2 }} />

                  {/* Tank Dimensions */}
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    📐 Kích thước Bể (m)
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        label="Chiều dài"
                        name="length"
                        type="number"
                        value={formData.length}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                        inputProps={{ step: 0.5 }}
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        label="Chiều rộng"
                        name="width"
                        type="number"
                        value={formData.width}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                        inputProps={{ step: 0.5 }}
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        label="Chiều sâu nước"
                        name="water_depth"
                        type="number"
                        value={formData.water_depth}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                        inputProps={{ step: 0.5 }}
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        label="Tổng chiều sâu"
                        name="total_depth"
                        type="number"
                        value={formData.total_depth}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                        inputProps={{ step: 0.5 }}
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        label="Dày thành"
                        name="wall_thickness"
                        type="number"
                        value={formData.wall_thickness}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                        inputProps={{ step: 0.05 }}
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        label="Dày đáy"
                        name="bottom_thickness"
                        type="number"
                        value={formData.bottom_thickness}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                        inputProps={{ step: 0.05 }}
                      />
                    </Grid>
                  </Grid>

                  <Divider sx={{ my: 2 }} />

                  {/* Reinforcement */}
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    🔩 Cốt thép
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        label="Ø Thép chính (mm)"
                        name="main_rebar_dia"
                        type="number"
                        value={formData.main_rebar_dia}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        label="a Thép chính (mm)"
                        name="main_rebar_spacing"
                        type="number"
                        value={formData.main_rebar_spacing}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        label="Ø Thép phân bố (mm)"
                        name="dist_rebar_dia"
                        type="number"
                        value={formData.dist_rebar_dia}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        label="a Thép phân bố (mm)"
                        name="dist_rebar_spacing"
                        type="number"
                        value={formData.dist_rebar_spacing}
                        onChange={handleChange}
                        margin="dense"
                        size="small"
                      />
                    </Grid>
                  </Grid>

                  <Divider sx={{ my: 2 }} />

                  {/* Options */}
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    ⚙️ Tùy chọn
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    <FormControlLabel
                      control={<Switch checked={formData.include_plan} onChange={handleChange} name="include_plan" />}
                      label="Mặt bằng"
                    />
                    <FormControlLabel
                      control={<Switch checked={formData.include_section} onChange={handleChange} name="include_section" />}
                      label="Mặt cắt"
                    />
                    <FormControlLabel
                      control={<Switch checked={formData.include_rebar} onChange={handleChange} name="include_rebar" />}
                      label="Chi tiết thép"
                    />
                  </Box>

                  {/* Error */}
                  {error && (
                    <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
                      {error}
                    </Alert>
                  )}

                  {/* Submit */}
                  <Button
                    type="submit"
                    variant="contained"
                    fullWidth
                    size="large"
                    sx={{ mt: 3 }}
                    disabled={loading}
                    startIcon={loading ? <CircularProgress size={20} /> : <CADIcon />}
                  >
                    {loading ? 'Đang tạo bản vẽ...' : 'Tạo Bản vẽ DXF'}
                  </Button>
                </Box>
              )}

              {activeTab === 1 && result && (
                <Box>
                  <Alert severity="success" sx={{ mb: 2 }}>
                    <strong>Thành công!</strong> Bản vẽ đã được tạo.
                  </Alert>

                  <Typography variant="subtitle2" gutterBottom>Thông tin:</Typography>
                  <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, mb: 2 }}>
                    <Typography variant="body2">Job ID: {result.job_id}</Typography>
                    <Typography variant="body2">File: {result.file_name}</Typography>
                  </Box>

                  <Button
                    variant="contained"
                    fullWidth
                    startIcon={<DownloadIcon />}
                    href={result.download_url}
                  >
                    Tải bản vẽ DXF
                  </Button>
                </Box>
              )}

              {activeTab === 2 && result && (
                <CADValidation validation={result.validation} />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Right - Preview */}
        <Grid item xs={12} md={7}>
          <DXFPreview
            dimensions={{
              length: formData.length,
              width: formData.width,
              depth: formData.water_depth,
              total_depth: formData.total_depth,
            }}
            type="tank"
            title={formData.drawing_title || 'Preview Bản vẽ'}
            downloadUrl={result?.download_url}
          />

          {/* Layer Info */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <LayersIcon fontSize="small" sx={{ mr: 0.5, color: 'primary.main' }} />
                <Typography variant="subtitle2">Layers theo chuẩn TCVN</Typography>
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                <Chip size="small" label="TANK_WALL" sx={{ bgcolor: '#808080', color: 'white' }} />
                <Chip size="small" label="TANK_WATER" sx={{ bgcolor: '#00BFFF', color: 'white' }} />
                <Chip size="small" label="REBAR_MAIN" sx={{ bgcolor: '#FF0000', color: 'white' }} />
                <Chip size="small" label="REBAR_DIST" sx={{ bgcolor: '#FF6600', color: 'white' }} />
                <Chip size="small" label="DIMENSION" sx={{ bgcolor: '#00FF00', color: 'black' }} />
                <Chip size="small" label="TEXT" sx={{ bgcolor: '#FFFF00', color: 'black' }} />
                <Chip size="small" label="HATCH" variant="outlined" />
                <Chip size="small" label="CENTERLINE" variant="outlined" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default CADPage;
