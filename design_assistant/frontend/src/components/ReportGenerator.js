/**
 * ReportGenerator Component
 * Tạo báo cáo PDF kỹ thuật (Sprint 4)
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Grid,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Card,
  CardContent,
  Chip,
} from '@mui/material';
import {
  PictureAsPdf as PDFIcon,
  Download as DownloadIcon,
  Description as ReportIcon,
  Calculate as CalcIcon,
} from '@mui/icons-material';
import { reportAPI } from '../services/api';

const ReportGenerator = ({ designData, calculationLog }) => {
  const [generating, setGenerating] = useState(false);
  const [reportResult, setReportResult] = useState(null);
  const [error, setError] = useState(null);
  const [reportType, setReportType] = useState('technical');
  
  const [formData, setFormData] = useState({
    project_name: designData?.project_name || '',
    project_code: '',
    client: '',
    location: '',
    prepared_by: 'HydroDraft',
    checked_by: '',
    approved_by: '',
    language: 'vi',
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleGenerateTechnical = async () => {
    if (!formData.project_name) {
      setError('Vui lòng nhập tên dự án');
      return;
    }

    setGenerating(true);
    setError(null);

    try {
      const response = await reportAPI.generateTechnicalReport({
        ...formData,
        project_data: {
          design_type: designData?.tank_type || 'tank',
          dimensions: designData?.dimensions,
          hydraulics: designData?.hydraulic_results,
        },
        calculation_results: calculationLog || {},
        output_files: designData?.drawing_file ? [{
          type: 'drawing',
          path: designData.drawing_file,
        }] : null,
      });

      setReportResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Lỗi khi tạo báo cáo');
    } finally {
      setGenerating(false);
    }
  };

  const handleGenerateCalculation = async () => {
    if (!formData.project_name || !calculationLog) {
      setError('Cần có dữ liệu tính toán để tạo phụ lục');
      return;
    }

    setGenerating(true);
    setError(null);

    try {
      const response = await reportAPI.generateCalculationReport(
        formData.project_name,
        calculationLog
      );

      setReportResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Lỗi khi tạo phụ lục tính toán');
    } finally {
      setGenerating(false);
    }
  };

  const handleGenerate = () => {
    if (reportType === 'technical') {
      handleGenerateTechnical();
    } else {
      handleGenerateCalculation();
    }
  };

  return (
    <Paper elevation={0} sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 2 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <ReportIcon color="primary" sx={{ mr: 1, fontSize: 28 }} />
        <Typography variant="h6">Tạo Báo cáo</Typography>
        <Chip 
          size="small" 
          label="PDF Format" 
          sx={{ ml: 'auto' }} 
          color="error" 
          variant="outlined"
          icon={<PDFIcon />}
        />
      </Box>

      {/* Report Type Selection */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card 
            variant={reportType === 'technical' ? 'elevation' : 'outlined'}
            sx={{ 
              cursor: 'pointer',
              border: reportType === 'technical' ? '2px solid' : '1px solid',
              borderColor: reportType === 'technical' ? 'primary.main' : 'divider',
            }}
            onClick={() => setReportType('technical')}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ReportIcon color={reportType === 'technical' ? 'primary' : 'action'} sx={{ mr: 1 }} />
                <Typography variant="subtitle1">Báo cáo Kỹ thuật</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Báo cáo đầy đủ bao gồm thuyết minh, thông số, bản vẽ và tính toán.
                Phù hợp nộp cơ quan thẩm định.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card 
            variant={reportType === 'calculation' ? 'elevation' : 'outlined'}
            sx={{ 
              cursor: 'pointer',
              border: reportType === 'calculation' ? '2px solid' : '1px solid',
              borderColor: reportType === 'calculation' ? 'primary.main' : 'divider',
            }}
            onClick={() => setReportType('calculation')}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CalcIcon color={reportType === 'calculation' ? 'primary' : 'action'} sx={{ mr: 1 }} />
                <Typography variant="subtitle1">Phụ lục Tính toán</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Chi tiết từng bước tính toán với công thức, thông số và tham chiếu tiêu chuẩn.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Divider sx={{ my: 2 }} />

      {/* Form */}
      <Typography variant="subtitle2" gutterBottom>
        Thông tin Báo cáo
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
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
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Mã dự án"
            name="project_code"
            value={formData.project_code}
            onChange={handleChange}
            margin="dense"
            size="small"
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Chủ đầu tư"
            name="client"
            value={formData.client}
            onChange={handleChange}
            margin="dense"
            size="small"
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Địa điểm"
            name="location"
            value={formData.location}
            onChange={handleChange}
            margin="dense"
            size="small"
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            label="Người lập"
            name="prepared_by"
            value={formData.prepared_by}
            onChange={handleChange}
            margin="dense"
            size="small"
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            label="Người kiểm tra"
            name="checked_by"
            value={formData.checked_by}
            onChange={handleChange}
            margin="dense"
            size="small"
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            label="Người phê duyệt"
            name="approved_by"
            value={formData.approved_by}
            onChange={handleChange}
            margin="dense"
            size="small"
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <FormControl fullWidth margin="dense" size="small">
            <InputLabel>Ngôn ngữ</InputLabel>
            <Select
              name="language"
              value={formData.language}
              label="Ngôn ngữ"
              onChange={handleChange}
            >
              <MenuItem value="vi">🇻🇳 Tiếng Việt</MenuItem>
              <MenuItem value="en">🇬🇧 English</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Generate Button */}
      <Box sx={{ mt: 3 }}>
        <Button
          fullWidth
          variant="contained"
          size="large"
          onClick={handleGenerate}
          disabled={generating}
          startIcon={generating ? <CircularProgress size={20} /> : <PDFIcon />}
        >
          {generating ? 'Đang tạo báo cáo...' : `Tạo ${reportType === 'technical' ? 'Báo cáo Kỹ thuật' : 'Phụ lục Tính toán'}`}
        </Button>
      </Box>

      {/* Result */}
      {reportResult && (
        <Alert 
          severity="success" 
          sx={{ mt: 2 }}
          action={
            <Button
              color="inherit"
              size="small"
              startIcon={<DownloadIcon />}
              href={reportAPI.downloadReport(reportResult.file_name)}
              target="_blank"
            >
              Tải PDF
            </Button>
          }
        >
          Báo cáo đã được tạo thành công: <strong>{reportResult.file_name}</strong>
        </Alert>
      )}
    </Paper>
  );
};

export default ReportGenerator;
