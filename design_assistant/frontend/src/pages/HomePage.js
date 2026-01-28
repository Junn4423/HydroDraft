import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  CardActionArea,
  Grid,
  Typography,
  Container,
  Chip,
  Alert,
  Paper,
  Divider,
} from '@mui/material';
import {
  Pool as PoolIcon,
  Timeline as TimelineIcon,
  Opacity as OpacityIcon,
  Description as DescriptionIcon,
  Draw as CADIcon,
  Architecture as BIMIcon,
  History as HistoryIcon,
  ViewInAr as ViewerIcon,
  CheckCircle as OKIcon,
  Water as WaterIcon,
  Gavel as StandardsIcon,
  RocketLaunch as SprintIcon,
} from '@mui/icons-material';
import { systemAPI, sprint4API } from '../services/api';

const features = [
  {
    title: 'Thiết kế Bể',
    description: 'Bể lắng, bể lọc, bể chứa, bể điều hòa. Tự động tính toán thủy lực và kết cấu.',
    icon: <PoolIcon sx={{ fontSize: 60 }} />,
    path: '/design/tank',
    color: '#1976d2',
    sprint: 2,
  },
  {
    title: 'Thiết kế Đường ống',
    description: 'Mạng lưới thoát nước, cấp nước. Thiết kế trắc dọc và bố trí giếng thăm.',
    icon: <TimelineIcon sx={{ fontSize: 60 }} />,
    path: '/design/pipeline',
    color: '#388e3c',
    sprint: 2,
  },
  {
    title: 'Thiết kế Giếng',
    description: 'Giếng quan trắc nước ngầm. Thiết kế cấu trúc và chọn vật liệu.',
    icon: <OpacityIcon sx={{ fontSize: 60 }} />,
    path: '/design/well',
    color: '#f57c00',
    sprint: 2,
  },
  {
    title: 'CAD Chuyên nghiệp',
    description: 'Bản vẽ kỹ thuật tiêu chuẩn TCVN với blocks, layers và annotations.',
    icon: <CADIcon sx={{ fontSize: 60 }} />,
    path: '/cad',
    color: '#9c27b0',
    sprint: 3,
    isNew: true,
  },
  {
    title: 'BIM Export',
    description: 'Xuất dữ liệu BIM cho Revit thông qua Dynamo và pyRevit.',
    icon: <BIMIcon sx={{ fontSize: 60 }} />,
    path: '/bim',
    color: '#e91e63',
    sprint: 4,
    isNew: true,
  },
  {
    title: 'Báo cáo PDF',
    description: 'Tạo báo cáo kỹ thuật và phụ lục tính toán để nộp thẩm định.',
    icon: <DescriptionIcon sx={{ fontSize: 60 }} />,
    path: '/reports',
    color: '#00bcd4',
    sprint: 4,
    isNew: true,
  },
  {
    title: 'Quản lý Version',
    description: 'Version control cho thiết kế. So sánh, rollback và audit trail.',
    icon: <HistoryIcon sx={{ fontSize: 60 }} />,
    path: '/versions',
    color: '#ff5722',
    sprint: 4,
    isNew: true,
  },
  {
    title: 'Trình xem 3D',
    description: 'Xem mô hình IFC trực tiếp trong trình duyệt không cần cài đặt.',
    icon: <ViewerIcon sx={{ fontSize: 60 }} />,
    path: '/viewer',
    color: '#607d8b',
    sprint: 4,
    isNew: true,
  },
];

function HomePage() {
  const navigate = useNavigate();
  const [systemStatus, setSystemStatus] = useState({ ok: true, version: '' });

  useEffect(() => {
    checkSystem();
  }, []);

  const checkSystem = async () => {
    try {
      const response = await systemAPI.healthCheck();
      setSystemStatus({
        ok: true,
        version: response.data?.version || '2.0.0',
      });
    } catch (err) {
      setSystemStatus({ ok: false, version: '' });
    }
  };

  return (
    <Container maxWidth="lg">
      {/* Header */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
          <WaterIcon sx={{ fontSize: 48, color: 'primary.main', mr: 1 }} />
          <Typography variant="h3" component="h1" sx={{ fontWeight: 'bold' }}>
            HydroDraft
          </Typography>
        </Box>
        <Typography variant="h6" color="text.secondary">
          Nền tảng Thiết kế Hạ tầng Môi trường Chuyên nghiệp
        </Typography>
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 1 }}>
          <Chip icon={<OKIcon />} label="Offline Mode" color="success" />
          <Chip label={`v${systemStatus.version}`} variant="outlined" />
          <Chip label="Production Ready" color="primary" />
        </Box>
      </Box>

      {/* Sprint Status */}
      <Alert severity="success" sx={{ mb: 4 }}>
        <Typography variant="body2">
          <strong>Tất cả 4 Sprint đã hoàn thành!</strong> Hệ thống đã sẵn sàng cho production.
          Bao gồm: Offline Foundation, Traceable Calculations, Professional CAD, và BIM Integration.
        </Typography>
      </Alert>

      {/* Feature Cards */}
      <Grid container spacing={3}>
        {features.map((feature) => (
          <Grid item xs={12} sm={6} md={3} key={feature.title}>
            <Card
              sx={{
                height: '100%',
                transition: 'transform 0.2s, box-shadow 0.2s',
                position: 'relative',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6,
                },
              }}
            >
              {feature.isNew && (
                <Chip
                  label="New"
                  color="secondary"
                  size="small"
                  sx={{ position: 'absolute', top: 8, right: 8, zIndex: 1 }}
                />
              )}
              <CardActionArea
                onClick={() => navigate(feature.path)}
                sx={{ height: '100%', p: 2 }}
              >
                <CardContent sx={{ textAlign: 'center' }}>
                  <Box sx={{ color: feature.color, mb: 2 }}>
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" component="h2" gutterBottom>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {feature.description}
                  </Typography>
                  <Chip 
                    label={`Sprint ${feature.sprint}`} 
                    size="small" 
                    sx={{ mt: 1 }}
                    variant="outlined"
                  />
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Standards */}
      <Paper sx={{ mt: 6, p: 3, bgcolor: 'primary.dark', color: 'white', borderRadius: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <StandardsIcon sx={{ mr: 1 }} />
          <Typography variant="h6">
            Tiêu chuẩn áp dụng
          </Typography>
        </Box>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <Typography variant="body2">
              <strong>TCVN 7957:2008</strong><br />
              Thoát nước - Mạng lưới và công trình bên ngoài
            </Typography>
          </Grid>
          <Grid item xs={12} md={3}>
            <Typography variant="body2">
              <strong>TCVN 33:2006</strong><br />
              Cấp nước - Mạng lưới đường ống và công trình
            </Typography>
          </Grid>
          <Grid item xs={12} md={3}>
            <Typography variant="body2">
              <strong>TCVN 5574:2018</strong><br />
              Kết cấu bê tông và bê tông cốt thép
            </Typography>
          </Grid>
          <Grid item xs={12} md={3}>
            <Typography variant="body2">
              <strong>QCVN 14:2008/BTNMT</strong><br />
              Quy chuẩn về nước thải sinh hoạt
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Sprints Summary */}
      <Box sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <SprintIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6">
            Các Sprint đã triển khai
          </Typography>
        </Box>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, bgcolor: 'success.light' }}>
              <Typography variant="subtitle2">Sprint 1</Typography>
              <Typography variant="body2">Offline Foundation</Typography>
              <Chip icon={<OKIcon />} label="Complete" size="small" color="success" sx={{ mt: 1 }} />
            </Paper>
          </Grid>
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, bgcolor: 'success.light' }}>
              <Typography variant="subtitle2">Sprint 2</Typography>
              <Typography variant="body2">Traceable Engineering</Typography>
              <Chip icon={<OKIcon />} label="Complete" size="small" color="success" sx={{ mt: 1 }} />
            </Paper>
          </Grid>
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, bgcolor: 'success.light' }}>
              <Typography variant="subtitle2">Sprint 3</Typography>
              <Typography variant="body2">Professional CAD</Typography>
              <Chip icon={<OKIcon />} label="Complete" size="small" color="success" sx={{ mt: 1 }} />
            </Paper>
          </Grid>
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, bgcolor: 'success.light' }}>
              <Typography variant="subtitle2">Sprint 4</Typography>
              <Typography variant="body2">BIM & Enterprise</Typography>
              <Chip icon={<OKIcon />} label="Complete" size="small" color="success" sx={{ mt: 1 }} />
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
}

export default HomePage;
