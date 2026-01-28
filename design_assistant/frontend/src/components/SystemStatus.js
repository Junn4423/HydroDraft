/**
 * SystemStatus Component
 * Hiển thị trạng thái hệ thống và database (Sprint 1)
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  LinearProgress,
  Alert,
  Grid,
  Tooltip,
} from '@mui/material';
import {
  Storage as DatabaseIcon,
  Cloud as ServerIcon,
  CheckCircle as OKIcon,
  Error as ErrorIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Computer as ComputerIcon,
} from '@mui/icons-material';
import { systemAPI } from '../services/api';

const SystemStatus = ({ compact = false }) => {
  const [status, setStatus] = useState({
    api: 'checking',
    database: 'checking',
    version: '',
    uptime: 0,
    memory: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const response = await systemAPI.healthCheck();
      setStatus({
        api: 'ok',
        database: response.data.database?.status || 'ok',
        version: response.data.version || 'unknown',
        uptime: response.data.uptime || 0,
        memory: response.data.memory_usage || 0,
        dbPath: response.data.database?.path || '',
        dbSize: response.data.database?.size || 0,
      });
    } catch (err) {
      setStatus(prev => ({
        ...prev,
        api: 'error',
      }));
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (s) => {
    if (s === 'ok' || s === 'connected') return 'success';
    if (s === 'checking') return 'warning';
    return 'error';
  };

  const getStatusIcon = (s) => {
    if (s === 'ok' || s === 'connected') return <OKIcon color="success" fontSize="small" />;
    if (s === 'checking') return <LinearProgress sx={{ width: 20 }} />;
    return <ErrorIcon color="error" fontSize="small" />;
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatUptime = (seconds) => {
    if (!seconds) return '0s';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  };

  if (compact) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Tooltip title={`API: ${status.api}`}>
          <Chip
            size="small"
            icon={getStatusIcon(status.api)}
            label="API"
            color={getStatusColor(status.api)}
            variant="outlined"
          />
        </Tooltip>
        <Tooltip title={`Database: ${status.database}`}>
          <Chip
            size="small"
            icon={<DatabaseIcon fontSize="small" />}
            label="DB"
            color={getStatusColor(status.database)}
            variant="outlined"
          />
        </Tooltip>
        {status.version && (
          <Chip
            size="small"
            label={`v${status.version}`}
            variant="outlined"
          />
        )}
      </Box>
    );
  }

  return (
    <Paper elevation={0} sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <ComputerIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6">Trạng thái Hệ thống</Typography>
      </Box>

      {loading ? (
        <LinearProgress />
      ) : (
        <Grid container spacing={2}>
          {/* API Status */}
          <Grid item xs={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <ServerIcon color={getStatusColor(status.api)} sx={{ fontSize: 40 }} />
              <Typography variant="subtitle2">API Server</Typography>
              <Chip
                size="small"
                label={status.api === 'ok' ? 'Hoạt động' : 'Lỗi'}
                color={getStatusColor(status.api)}
              />
            </Paper>
          </Grid>

          {/* Database Status */}
          <Grid item xs={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <DatabaseIcon color={getStatusColor(status.database)} sx={{ fontSize: 40 }} />
              <Typography variant="subtitle2">SQLite Database</Typography>
              <Chip
                size="small"
                label={status.database === 'ok' ? 'Kết nối' : 'Lỗi'}
                color={getStatusColor(status.database)}
              />
              {status.dbSize > 0 && (
                <Typography variant="caption" display="block" color="text.secondary">
                  {formatBytes(status.dbSize)}
                </Typography>
              )}
            </Paper>
          </Grid>

          {/* Version */}
          <Grid item xs={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <SpeedIcon color="primary" sx={{ fontSize: 40 }} />
              <Typography variant="subtitle2">Phiên bản</Typography>
              <Typography variant="h6" color="primary">
                {status.version || '—'}
              </Typography>
            </Paper>
          </Grid>

          {/* Uptime */}
          <Grid item xs={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <MemoryIcon color="info" sx={{ fontSize: 40 }} />
              <Typography variant="subtitle2">Uptime</Typography>
              <Typography variant="h6" color="info.main">
                {formatUptime(status.uptime)}
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Offline mode indicator */}
      <Alert severity="success" sx={{ mt: 2 }} icon={<OKIcon />}>
        <strong>Chế độ Offline</strong> - Hệ thống hoạt động hoàn toàn độc lập, không cần kết nối Internet.
      </Alert>
    </Paper>
  );
};

export default SystemStatus;
