/**
 * VersionHistory Component
 * Hiển thị lịch sử phiên bản và so sánh (Sprint 4)
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  LinearProgress,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
} from '@mui/lab';
import {
  History as HistoryIcon,
  Compare as CompareIcon,
  Restore as RestoreIcon,
  Check as CheckIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon,
  Tag as TagIcon,
  Add as AddIcon,
  Remove as RemoveIcon,
  VerifiedUser as ApprovedIcon,
} from '@mui/icons-material';
import { versionAPI } from '../services/api';

const VersionHistory = ({ projectId, onVersionSelect, onRollback }) => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedVersions, setSelectedVersions] = useState([]);
  const [compareDialog, setCompareDialog] = useState(false);
  const [compareResult, setCompareResult] = useState(null);
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    if (projectId) {
      loadVersions();
    }
  }, [projectId]);

  const loadVersions = async () => {
    setLoading(true);
    try {
      const response = await versionAPI.listVersions(projectId);
      setVersions(response.data.versions || []);
    } catch (error) {
      console.error('Failed to load versions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectVersion = (version) => {
    if (selectedVersions.includes(version.version_id)) {
      setSelectedVersions(selectedVersions.filter(v => v !== version.version_id));
    } else if (selectedVersions.length < 2) {
      setSelectedVersions([...selectedVersions, version.version_id]);
    }
  };

  const handleCompare = async () => {
    if (selectedVersions.length !== 2) return;
    
    setComparing(true);
    setCompareDialog(true);
    
    try {
      const response = await versionAPI.compareVersions({
        version_from: selectedVersions[0],
        version_to: selectedVersions[1],
      });
      setCompareResult(response.data);
    } catch (error) {
      console.error('Compare failed:', error);
    } finally {
      setComparing(false);
    }
  };

  const handleRollback = async (versionId) => {
    if (!window.confirm('Bạn có chắc muốn khôi phục về phiên bản này?')) return;
    
    try {
      await versionAPI.rollbackVersion(projectId, versionId);
      loadVersions();
      if (onRollback) onRollback(versionId);
    } catch (error) {
      console.error('Rollback failed:', error);
    }
  };

  const handleApprove = async (versionId) => {
    const approvedBy = prompt('Nhập tên người phê duyệt:');
    if (!approvedBy) return;
    
    try {
      await versionAPI.approveVersion(versionId, approvedBy);
      loadVersions();
    } catch (error) {
      console.error('Approve failed:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'success';
      case 'draft': return 'default';
      case 'rollback': return 'warning';
      default: return 'default';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <Box sx={{ textAlign: 'center', p: 3 }}>
        <CircularProgress />
        <Typography variant="body2" sx={{ mt: 1 }}>Đang tải lịch sử...</Typography>
      </Box>
    );
  }

  if (!projectId) {
    return (
      <Alert severity="info">
        Chọn một dự án để xem lịch sử phiên bản.
      </Alert>
    );
  }

  return (
    <Paper elevation={0} sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 2 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <HistoryIcon color="primary" sx={{ mr: 1 }} />
        <Typography variant="h6">Lịch sử Phiên bản</Typography>
        <Chip 
          size="small" 
          label={`${versions.length} phiên bản`} 
          sx={{ ml: 'auto', mr: 1 }} 
          color="primary" 
          variant="outlined"
        />
        {selectedVersions.length === 2 && (
          <Button
            size="small"
            variant="contained"
            startIcon={<CompareIcon />}
            onClick={handleCompare}
          >
            So sánh
          </Button>
        )}
      </Box>

      {versions.length === 0 ? (
        <Alert severity="info">
          Chưa có phiên bản nào. Các thiết kế sẽ được lưu tự động.
        </Alert>
      ) : (
        <Timeline position="right" sx={{ p: 0 }}>
          {versions.map((version, index) => (
            <TimelineItem key={version.version_id}>
              <TimelineOppositeContent sx={{ maxWidth: 100, pr: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  {formatDate(version.created_at)}
                </Typography>
              </TimelineOppositeContent>
              
              <TimelineSeparator>
                <TimelineDot 
                  color={selectedVersions.includes(version.version_id) ? 'secondary' : getStatusColor(version.status)}
                  sx={{ cursor: 'pointer' }}
                  onClick={() => handleSelectVersion(version)}
                >
                  {version.status === 'approved' ? <ApprovedIcon /> : <ScheduleIcon />}
                </TimelineDot>
                {index < versions.length - 1 && <TimelineConnector />}
              </TimelineSeparator>
              
              <TimelineContent>
                <Paper 
                  sx={{ 
                    p: 1.5, 
                    bgcolor: selectedVersions.includes(version.version_id) ? 'secondary.light' : 'white',
                    cursor: 'pointer'
                  }}
                  onClick={() => onVersionSelect && onVersionSelect(version)}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <TagIcon fontSize="small" color="action" />
                    <Typography variant="subtitle2">
                      {version.version_tag || version.version_id.slice(0, 8)}
                    </Typography>
                    <Chip 
                      size="small" 
                      label={version.status} 
                      color={getStatusColor(version.status)}
                    />
                  </Box>
                  
                  {version.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {version.description}
                    </Typography>
                  )}
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <PersonIcon fontSize="small" color="action" />
                    <Typography variant="caption" color="text.secondary">
                      {version.created_by || 'System'}
                    </Typography>
                    
                    <Box sx={{ ml: 'auto' }}>
                      <Tooltip title="Khôi phục">
                        <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleRollback(version.version_id); }}>
                          <RestoreIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      {version.status !== 'approved' && (
                        <Tooltip title="Phê duyệt">
                          <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleApprove(version.version_id); }}>
                            <CheckIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </Box>
                </Paper>
              </TimelineContent>
            </TimelineItem>
          ))}
        </Timeline>
      )}

      {/* Compare Dialog */}
      <Dialog open={compareDialog} onClose={() => setCompareDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <CompareIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          So sánh Phiên bản
        </DialogTitle>
        <DialogContent>
          {comparing ? (
            <Box sx={{ textAlign: 'center', p: 4 }}>
              <CircularProgress />
              <Typography sx={{ mt: 2 }}>Đang so sánh...</Typography>
            </Box>
          ) : compareResult ? (
            <>
              {/* Summary */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>Tổng quan thay đổi</Typography>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Chip 
                    icon={<AddIcon />} 
                    label={`${compareResult.added?.length || 0} thêm mới`} 
                    color="success" 
                    variant="outlined"
                  />
                  <Chip 
                    icon={<RemoveIcon />} 
                    label={`${compareResult.removed?.length || 0} xóa bỏ`} 
                    color="error" 
                    variant="outlined"
                  />
                  <Chip 
                    label={`${compareResult.modified?.length || 0} thay đổi`} 
                    color="warning" 
                    variant="outlined"
                  />
                </Box>
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Changes Table */}
              {compareResult.modified && compareResult.modified.length > 0 && (
                <>
                  <Typography variant="subtitle2" gutterBottom>Chi tiết thay đổi</Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Thông số</TableCell>
                          <TableCell>Giá trị cũ</TableCell>
                          <TableCell>Giá trị mới</TableCell>
                          <TableCell>% Thay đổi</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {compareResult.modified.map((item, i) => (
                          <TableRow key={i}>
                            <TableCell>{item.param || item.key}</TableCell>
                            <TableCell sx={{ color: 'error.main' }}>{item.old_value}</TableCell>
                            <TableCell sx={{ color: 'success.main' }}>{item.new_value}</TableCell>
                            <TableCell>
                              {item.percent_change !== undefined && (
                                <Chip 
                                  size="small" 
                                  label={`${item.percent_change > 0 ? '+' : ''}${item.percent_change.toFixed(1)}%`}
                                  color={item.percent_change > 0 ? 'success' : 'error'}
                                />
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </>
              )}
            </>
          ) : (
            <Alert severity="error">Không thể so sánh phiên bản</Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompareDialog(false)}>Đóng</Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default VersionHistory;
