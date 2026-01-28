/**
 * Version History Page
 * Quản lý phiên bản thiết kế (Sprint 4)
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
  TextField,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  History as HistoryIcon,
  Add as AddIcon,
  Compare as CompareIcon,
  Restore as RestoreIcon,
  CheckCircle as ApproveIcon,
  Storage as StorageIcon,
  Folder as FolderIcon,
  AutoAwesome as FeaturesIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import VersionHistory from '../components/VersionHistory';

const VersionsPage = () => {
  const [projectId, setProjectId] = useState('');
  const [selectedProject, setSelectedProject] = useState(null);

  const recentProjects = [
    { id: 'XLNT-2024-001', name: 'Trạm XLNT TP XYZ', versions: 5 },
    { id: 'CAP-2024-002', name: 'Hệ thống cấp nước ABC', versions: 3 },
    { id: 'THOAT-2024-003', name: 'Thoát nước KCN DEF', versions: 8 },
  ];

  const handleSelectProject = (project) => {
    setSelectedProject(project);
    setProjectId(project.id);
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <HistoryIcon color="primary" sx={{ fontSize: 40, mr: 2 }} />
        <Box>
          <Typography variant="h4">Quản lý Phiên bản</Typography>
          <Typography variant="body2" color="text.secondary">
            Version control cho thiết kế kỹ thuật - so sánh, rollback và audit trail
          </Typography>
        </Box>
        <Chip label="Sprint 4" color="secondary" sx={{ ml: 'auto' }} />
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>Engineering Version Control</strong> - Mỗi lần thiết kế sẽ tạo một phiên bản mới với đầy đủ 
          thông tin: input parameters, calculation logs, output files, và metadata.
        </Typography>
      </Alert>

      <Grid container spacing={3}>
        {/* Left - Project Selection */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <FolderIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Chọn Dự án</Typography>
              </Box>
              
              <TextField
                fullWidth
                label="Project ID"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                margin="normal"
                size="small"
                placeholder="VD: XLNT-2024-001"
              />

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" gutterBottom>
                Dự án gần đây:
              </Typography>

              <List>
                {recentProjects.map((project) => (
                  <ListItem
                    key={project.id}
                    button
                    selected={selectedProject?.id === project.id}
                    onClick={() => handleSelectProject(project)}
                    sx={{ borderRadius: 1, mb: 0.5 }}
                  >
                    <ListItemIcon>
                      <StorageIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={project.name}
                      secondary={`${project.id} • ${project.versions} phiên bản`}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>

          {/* Features */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <FeaturesIcon sx={{ mr: 1, color: 'secondary.main' }} />
                <Typography variant="h6">Tính năng</Typography>
              </Box>
              <List dense>
                <ListItem>
                  <ListItemIcon><AddIcon color="primary" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Tự động tạo version" secondary="Mỗi lần thiết kế" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CompareIcon color="info" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="So sánh versions" secondary="Xem diff chi tiết" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><RestoreIcon color="warning" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Rollback" secondary="Khôi phục version cũ" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><ApproveIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Phê duyệt" secondary="Đánh dấu version chính thức" />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Right - Version History */}
        <Grid item xs={12} md={8}>
          <VersionHistory
            projectId={projectId || selectedProject?.id}
            onVersionSelect={(version) => console.log('Selected:', version)}
            onRollback={(versionId) => console.log('Rollback to:', versionId)}
          />

          {/* Version Details */}
          {selectedProject && (
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <AssessmentIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Dữ liệu lưu trữ mỗi version</Typography>
                </Box>
                <Grid container spacing={2}>
                  <Grid item xs={6} md={3}>
                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                      <Typography variant="h6" color="primary">Input</Typography>
                      <Typography variant="body2">Thông số đầu vào</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                      <Typography variant="h6" color="secondary">Calc Log</Typography>
                      <Typography variant="body2">Nhật ký tính toán</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                      <Typography variant="h6" color="success.main">Output</Typography>
                      <Typography variant="body2">File bản vẽ</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                      <Typography variant="h6" color="warning.main">Override</Typography>
                      <Typography variant="body2">Log vi phạm</Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default VersionsPage;
