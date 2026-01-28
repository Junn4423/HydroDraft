/**
 * BIMExport Component
 * Xuất BIM data và Revit bridge scripts (Sprint 4)
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Divider,
  LinearProgress,
} from '@mui/material';
import {
  Architecture as BIMIcon,
  Download as DownloadIcon,
  Code as CodeIcon,
  DataObject as JSONIcon,
  Description as ScriptIcon,
  CheckCircle as SuccessIcon,
  CloudDownload as CloudIcon,
  Pool as TankIcon,
  Business as ProjectIcon,
  Folder as FolderIcon,
  MenuBook as GuideIcon,
} from '@mui/icons-material';
import { bimAPI } from '../services/api';

const BIMExport = ({ designData, projectInfo }) => {
  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState(null);
  const [error, setError] = useState(null);

  const handleExportTank = async () => {
    if (!designData?.dimensions) {
      setError('Chưa có dữ liệu thiết kế. Vui lòng chạy thiết kế trước.');
      return;
    }

    setExporting(true);
    setError(null);

    try {
      const response = await bimAPI.exportTank({
        name: designData.tank_name || 'Tank-01',
        length: designData.dimensions.length,
        width: designData.dimensions.width,
        depth: designData.dimensions.total_depth || designData.dimensions.depth,
        wall_thickness: designData.dimensions.wall_thickness || 0.3,
        foundation_thickness: designData.dimensions.bottom_thickness || 0.4,
        tank_type: designData.tank_type || 'sedimentation',
        origin: [0, 0, 0],
        design_params: designData.hydraulic_results,
      });

      setExportResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Lỗi khi xuất BIM');
    } finally {
      setExporting(false);
    }
  };

  const handleExportProject = async () => {
    if (!projectInfo) {
      setError('Chưa có thông tin dự án.');
      return;
    }

    setExporting(true);
    setError(null);

    try {
      // Build project request from available data
      const tanks = designData ? [{
        name: designData.tank_name || 'Tank-01',
        length: designData.dimensions?.length || 10,
        width: designData.dimensions?.width || 5,
        depth: designData.dimensions?.total_depth || 4,
        wall_thickness: 0.3,
        foundation_thickness: 0.4,
        tank_type: designData.tank_type || 'sedimentation',
        origin: [0, 0, 0],
      }] : [];

      const response = await bimAPI.exportProject({
        project_name: projectInfo.project_name || 'HydroDraft Project',
        project_number: projectInfo.project_code || '',
        client: projectInfo.client || '',
        location: projectInfo.location || '',
        tanks: tanks,
        pipes: [],
      });

      setExportResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Lỗi khi xuất BIM');
    } finally {
      setExporting(false);
    }
  };

  const getFileIcon = (filename) => {
    if (filename?.includes('.json')) return <JSONIcon color="primary" />;
    if (filename?.includes('.dyn')) return <ScriptIcon color="secondary" />;
    if (filename?.includes('.py')) return <CodeIcon color="success" />;
    return <CloudIcon />;
  };

  const getFileName = (filepath) => {
    return filepath?.split('/').pop() || filepath;
  };

  return (
    <Paper elevation={0} sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 2 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <BIMIcon color="primary" sx={{ mr: 1, fontSize: 28 }} />
        <Typography variant="h6">BIM Export</Typography>
        <Chip 
          size="small" 
          label="Revit Compatible" 
          sx={{ ml: 'auto' }} 
          color="success" 
          variant="outlined"
        />
      </Box>

      {/* Description */}
      <Alert severity="info" sx={{ mb: 2 }}>
        <Typography variant="body2">
          Xuất dữ liệu BIM để sử dụng trong Revit thông qua Dynamo hoặc pyRevit.
          Các file tạo ra sẽ tạo đối tượng native trong Revit, có thể chỉnh sửa.
        </Typography>
      </Alert>

      {/* Export Buttons */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TankIcon fontSize="small" sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="subtitle1">
                  Xuất Bể đơn lẻ
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Xuất một bể với đầy đủ geometry và parameters.
              </Typography>
            </CardContent>
            <CardActions>
              <Button
                fullWidth
                variant="contained"
                onClick={handleExportTank}
                disabled={exporting || !designData?.dimensions}
                startIcon={exporting ? <CircularProgress size={18} /> : <DownloadIcon />}
              >
                {exporting ? 'Đang xuất...' : 'Xuất Tank BIM'}
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ProjectIcon fontSize="small" sx={{ mr: 1, color: 'secondary.main' }} />
                <Typography variant="subtitle1">
                  Xuất Dự án đầy đủ
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Xuất toàn bộ dự án với nhiều công trình.
              </Typography>
            </CardContent>
            <CardActions>
              <Button
                fullWidth
                variant="outlined"
                onClick={handleExportProject}
                disabled={exporting}
                startIcon={<DownloadIcon />}
              >
                Xuất Project BIM
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Export Result */}
      {exportResult && (
        <Box>
          <Alert severity="success" sx={{ mb: 2 }} icon={<SuccessIcon />}>
            Xuất BIM thành công! {exportResult.elements?.length || 1} đối tượng đã được tạo.
          </Alert>

          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <FolderIcon fontSize="small" sx={{ mr: 0.5, color: 'primary.main' }} />
            <Typography variant="subtitle2">Các file đã tạo:</Typography>
          </Box>

          <List>
            {exportResult.files && Object.entries(exportResult.files).map(([key, filepath]) => (
              <ListItem
                key={key}
                sx={{ bgcolor: 'white', mb: 1, borderRadius: 1 }}
                secondaryAction={
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<DownloadIcon />}
                    href={bimAPI.downloadFile(getFileName(filepath))}
                    target="_blank"
                  >
                    Tải về
                  </Button>
                }
              >
                <ListItemIcon>
                  {getFileIcon(filepath)}
                </ListItemIcon>
                <ListItemText
                  primary={key.replace(/_/g, ' ').toUpperCase()}
                  secondary={getFileName(filepath)}
                />
              </ListItem>
            ))}
          </List>

          <Divider sx={{ my: 2 }} />

          {/* Usage Instructions */}
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <GuideIcon fontSize="small" sx={{ mr: 0.5, color: 'info.main' }} />
            <Typography variant="subtitle2">Hướng dẫn sử dụng:</Typography>
          </Box>
          
          <Box sx={{ bgcolor: 'white', p: 2, borderRadius: 1 }}>
            <Typography variant="body2" paragraph>
              <strong>Dynamo (khuyến nghị):</strong>
            </Typography>
            <ol style={{ margin: 0, paddingLeft: 20 }}>
              <li>Mở Revit → Tab Manage → Dynamo</li>
              <li>Mở file .dyn đã tải về</li>
              <li>Cập nhật đường dẫn file BIM_Data.json</li>
              <li>Click Run để tạo đối tượng</li>
            </ol>

            <Typography variant="body2" paragraph sx={{ mt: 2 }}>
              <strong>pyRevit:</strong>
            </Typography>
            <ol style={{ margin: 0, paddingLeft: 20 }}>
              <li>Cài đặt pyRevit extension</li>
              <li>Copy file .py vào thư mục pyRevit</li>
              <li>Chạy script từ Revit</li>
            </ol>
          </Box>
        </Box>
      )}
    </Paper>
  );
};

export default BIMExport;
