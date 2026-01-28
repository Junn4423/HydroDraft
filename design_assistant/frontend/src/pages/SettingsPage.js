/**
 * Settings Page
 * Cài đặt hệ thống
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
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Storage as DatabaseIcon,
  Language as LanguageIcon,
  Palette as ThemeIcon,
  Backup as BackupIcon,
  RestoreFromTrash as RestoreIcon,
  CheckCircle as OKIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import SystemStatus from '../components/SystemStatus';

const SettingsPage = () => {
  const [settings, setSettings] = useState({
    autoOpenBrowser: true,
    autoSaveVersions: true,
    language: 'vi',
    theme: 'light',
    defaultScale: '1:100',
    outputFolder: './outputs',
  });

  const handleChange = (name, value) => {
    setSettings(prev => ({ ...prev, [name]: value }));
  };

  const handleBackup = () => {
    alert('Đang backup database...');
  };

  const handleRestore = () => {
    if (window.confirm('Bạn có chắc muốn restore database? Dữ liệu hiện tại sẽ bị ghi đè.')) {
      alert('Chọn file backup để restore...');
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <SettingsIcon color="primary" sx={{ fontSize: 40, mr: 2 }} />
        <Box>
          <Typography variant="h4">Cài đặt</Typography>
          <Typography variant="body2" color="text.secondary">
            Cấu hình hệ thống và tùy chỉnh
          </Typography>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* System Status */}
        <Grid item xs={12}>
          <SystemStatus />
        </Grid>

        {/* General Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                ⚙️ Cài đặt Chung
              </Typography>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoOpenBrowser}
                    onChange={(e) => handleChange('autoOpenBrowser', e.target.checked)}
                  />
                }
                label="Tự động mở trình duyệt khi khởi động"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoSaveVersions}
                    onChange={(e) => handleChange('autoSaveVersions', e.target.checked)}
                  />
                }
                label="Tự động lưu version mỗi thiết kế"
              />

              <Divider sx={{ my: 2 }} />

              <TextField
                fullWidth
                label="Thư mục xuất file"
                value={settings.outputFolder}
                onChange={(e) => handleChange('outputFolder', e.target.value)}
                margin="normal"
                size="small"
              />

              <TextField
                fullWidth
                label="Tỷ lệ mặc định"
                value={settings.defaultScale}
                onChange={(e) => handleChange('defaultScale', e.target.value)}
                margin="normal"
                size="small"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Database */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <DatabaseIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Database
              </Typography>

              <Alert severity="success" sx={{ mb: 2 }} icon={<OKIcon />}>
                SQLite database đang hoạt động bình thường
              </Alert>

              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="Vị trí" 
                    secondary="./data/design_data.db" 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Kích thước" 
                    secondary="2.5 MB" 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Số dự án" 
                    secondary="15" 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Số versions" 
                    secondary="48" 
                  />
                </ListItem>
              </List>

              <Divider sx={{ my: 2 }} />

              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<BackupIcon />}
                  onClick={handleBackup}
                >
                  Backup
                </Button>
                <Button
                  variant="outlined"
                  color="warning"
                  startIcon={<RestoreIcon />}
                  onClick={handleRestore}
                >
                  Restore
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* About */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <InfoIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Thông tin Ứng dụng
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <List dense>
                    <ListItem>
                      <ListItemText primary="Tên" secondary="HydroDraft Professional" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Phiên bản" secondary="2.0.0" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Build" secondary="Sprint 4 - Production" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Nền tảng" secondary="Windows x64" />
                    </ListItem>
                  </List>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Tính năng đã triển khai:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    <Chip size="small" label="Sprint 1 - Offline" color="success" />
                    <Chip size="small" label="Sprint 2 - Traceable" color="success" />
                    <Chip size="small" label="Sprint 3 - CAD Pro" color="success" />
                    <Chip size="small" label="Sprint 4 - BIM" color="success" />
                  </Box>

                  <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>
                    Tiêu chuẩn hỗ trợ:
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    TCVN 7957:2008 • TCVN 33:2006 • TCVN 5574:2018 • QCVN 14:2008/BTNMT
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default SettingsPage;
