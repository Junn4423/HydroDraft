/**
 * 3D Viewer Page
 * Trình xem IFC 3D (Sprint 4)
 */

import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
  Button,
  TextField,
  Divider,
} from '@mui/material';
import {
  ViewInAr as ViewerIcon,
  CloudUpload as UploadIcon,
  Download as DownloadIcon,
  FolderOpen as FolderOpenIcon,
  Gamepad as GamepadIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import IFCViewer from '../components/IFCViewer';

const ViewerPage = () => {
  const [ifcUrl, setIfcUrl] = useState('');

  const sampleModels = [
    { name: 'Bể lắng 01', url: '/models/tank_01.ifc' },
    { name: 'Trạm bơm', url: '/models/pump_station.ifc' },
    { name: 'Hệ thống ống', url: '/models/pipe_network.ifc' },
  ];

  return (
    <Container maxWidth="xl">
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <ViewerIcon color="primary" sx={{ fontSize: 40, mr: 2 }} />
        <Box>
          <Typography variant="h4">Trình xem 3D</Typography>
          <Typography variant="body2" color="text.secondary">
            Xem mô hình IFC trực tiếp trong trình duyệt - không cần cài đặt phần mềm
          </Typography>
        </Box>
        <Chip label="Sprint 4" color="secondary" sx={{ ml: 'auto' }} />
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>IFC.js Viewer</strong> - Hỗ trợ định dạng IFC2x3 và IFC4. 
          Cho phép xoay, zoom, cắt mặt cắt và xem thông tin chi tiết của từng đối tượng.
        </Typography>
      </Alert>

      <Grid container spacing={3}>
        {/* Left - Controls */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <FolderOpenIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Tải mô hình</Typography>
              </Box>

              <TextField
                fullWidth
                label="URL file IFC"
                value={ifcUrl}
                onChange={(e) => setIfcUrl(e.target.value)}
                margin="normal"
                size="small"
                placeholder="https://example.com/model.ifc"
              />

              <Button
                fullWidth
                variant="outlined"
                startIcon={<UploadIcon />}
                sx={{ mt: 1 }}
              >
                Upload từ máy
              </Button>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" gutterBottom>
                Mẫu có sẵn:
              </Typography>

              {sampleModels.map((model) => (
                <Button
                  key={model.name}
                  fullWidth
                  variant="text"
                  size="small"
                  onClick={() => setIfcUrl(model.url)}
                  sx={{ justifyContent: 'flex-start', mb: 0.5 }}
                >
                  {model.name}
                </Button>
              ))}
            </CardContent>
          </Card>

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <GamepadIcon sx={{ mr: 1, color: 'secondary.main' }} />
                <Typography variant="h6">Điều khiển</Typography>
              </Box>
              <Typography variant="body2" paragraph>
                <strong>Chuột trái:</strong> Xoay mô hình
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Chuột phải:</strong> Di chuyển
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Scroll:</strong> Zoom in/out
              </Typography>
              <Typography variant="body2">
                <strong>Click:</strong> Chọn đối tượng
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Right - Viewer */}
        <Grid item xs={12} md={9}>
          <IFCViewer ifcUrl={ifcUrl} />

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AssessmentIcon sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="h6">Thông tin mô hình</Typography>
              </Box>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                    <Typography variant="h5" color="primary">12</Typography>
                    <Typography variant="body2">Đối tượng</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                    <Typography variant="h5" color="secondary">3</Typography>
                    <Typography variant="body2">Levels</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                    <Typography variant="h5" color="success.main">5</Typography>
                    <Typography variant="body2">Materials</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                    <Typography variant="h5" color="warning.main">2.5MB</Typography>
                    <Typography variant="body2">File size</Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ViewerPage;
