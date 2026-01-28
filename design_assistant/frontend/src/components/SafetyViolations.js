/**
 * SafetyViolations Component
 * Hiển thị vi phạm tiêu chuẩn và cho phép override (Sprint 2)
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Alert,
  AlertTitle,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  LinearProgress,
  Divider,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Block as BlockIcon,
  Edit as EditIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';

const SafetyViolations = ({ 
  violations = [], 
  warnings = [], 
  canExport = true,
  onOverride,
  jobId 
}) => {
  const [openOverride, setOpenOverride] = useState(false);
  const [selectedViolation, setSelectedViolation] = useState(null);
  const [overrideForm, setOverrideForm] = useState({
    reason: '',
    engineer_id: '',
    engineer_name: '',
    reference_doc: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const handleOpenOverride = (violation) => {
    setSelectedViolation(violation);
    setOpenOverride(true);
  };

  const handleCloseOverride = () => {
    setOpenOverride(false);
    setSelectedViolation(null);
    setOverrideForm({
      reason: '',
      engineer_id: '',
      engineer_name: '',
      reference_doc: '',
    });
  };

  const handleOverrideSubmit = async () => {
    if (overrideForm.reason.length < 50) {
      alert('Lý do phải có ít nhất 50 ký tự');
      return;
    }

    setSubmitting(true);
    try {
      if (onOverride) {
        await onOverride({
          job_id: jobId,
          violation_id: selectedViolation.id,
          ...overrideForm,
        });
      }
      handleCloseOverride();
    } catch (error) {
      console.error('Override failed:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'info';
      default: return 'default';
    }
  };

  const hasIssues = violations.length > 0 || warnings.length > 0;

  return (
    <Paper elevation={0} sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 2 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <SecurityIcon color={hasIssues ? 'warning' : 'success'} sx={{ mr: 1 }} />
        <Typography variant="h6">Kiểm tra An toàn</Typography>
        <Chip
          size="small"
          label={canExport ? 'Cho phép xuất' : 'Bị chặn xuất'}
          color={canExport ? 'success' : 'error'}
          sx={{ ml: 'auto' }}
        />
      </Box>

      {/* No Issues */}
      {!hasIssues && (
        <Alert severity="success" icon={<CheckIcon />}>
          <AlertTitle>Đạt yêu cầu</AlertTitle>
          Tất cả các kiểm tra an toàn đều đạt. Có thể xuất bản vẽ và báo cáo.
        </Alert>
      )}

      {/* Violations - Critical */}
      {violations.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="error" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <BlockIcon fontSize="small" sx={{ mr: 0.5 }} />
            Vi phạm ({violations.length})
          </Typography>
          
          <List dense>
            {violations.map((v, index) => (
              <Paper key={index} sx={{ mb: 1, overflow: 'hidden' }}>
                <ListItem
                  sx={{ bgcolor: 'error.light' }}
                  secondaryAction={
                    !v.overridden && (
                      <Button
                        size="small"
                        variant="outlined"
                        color="error"
                        startIcon={<EditIcon />}
                        onClick={() => handleOpenOverride(v)}
                      >
                        Override
                      </Button>
                    )
                  }
                >
                  <ListItemIcon>
                    {v.overridden ? (
                      <CheckIcon color="warning" />
                    ) : (
                      <ErrorIcon color="error" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <span>{v.message || v.description}</span>
                        <Chip size="small" label={v.code || 'VIOLATION'} color="error" variant="outlined" />
                        {v.overridden && (
                          <Chip size="small" label="Đã override" color="warning" />
                        )}
                      </Box>
                    }
                    secondary={
                      <>
                        <Typography variant="caption" display="block">
                          📚 {v.reference || 'Tiêu chuẩn liên quan'}
                        </Typography>
                        {v.parameter && (
                          <Typography variant="caption" display="block">
                            Thông số: {v.parameter} | Giá trị: {v.actual_value} | Giới hạn: {v.limit_value}
                          </Typography>
                        )}
                        {v.overridden && v.override_info && (
                          <Alert severity="warning" sx={{ mt: 1 }} icon={false}>
                            <Typography variant="caption">
                              <strong>Override bởi:</strong> {v.override_info.engineer_name}<br />
                              <strong>Lý do:</strong> {v.override_info.reason}
                            </Typography>
                          </Alert>
                        )}
                      </>
                    }
                  />
                </ListItem>
              </Paper>
            ))}
          </List>
        </Box>
      )}

      {/* Warnings */}
      {warnings.length > 0 && (
        <Box>
          <Typography variant="subtitle2" color="warning.main" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <WarningIcon fontSize="small" sx={{ mr: 0.5 }} />
            Cảnh báo ({warnings.length})
          </Typography>
          
          <List dense>
            {warnings.map((w, index) => (
              <ListItem key={index} sx={{ bgcolor: 'warning.light', borderRadius: 1, mb: 0.5 }}>
                <ListItemIcon>
                  <WarningIcon color="warning" />
                </ListItemIcon>
                <ListItemText
                  primary={typeof w === 'object' ? w.message : w}
                  secondary={typeof w === 'object' ? w.reference : null}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {/* Export Status */}
      {!canExport && (
        <Alert severity="error" sx={{ mt: 2 }}>
          <AlertTitle>Không thể xuất file</AlertTitle>
          Còn {violations.filter(v => !v.overridden).length} vi phạm chưa được xử lý. 
          Vui lòng override với lý do hợp lệ hoặc điều chỉnh thông số thiết kế.
        </Alert>
      )}

      {/* Override Dialog */}
      <Dialog open={openOverride} onClose={handleCloseOverride} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ bgcolor: 'error.light' }}>
          ⚠️ Override Vi phạm
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          {selectedViolation && (
            <>
              <Alert severity="error" sx={{ mb: 2 }}>
                <AlertTitle>{selectedViolation.code}</AlertTitle>
                {selectedViolation.message || selectedViolation.description}
              </Alert>

              <Typography variant="body2" color="text.secondary" paragraph>
                Override yêu cầu lý do chi tiết và thông tin kỹ sư chịu trách nhiệm. 
                Hành động này sẽ được ghi log.
              </Typography>

              <Divider sx={{ my: 2 }} />

              <TextField
                fullWidth
                label="ID Kỹ sư"
                value={overrideForm.engineer_id}
                onChange={(e) => setOverrideForm({ ...overrideForm, engineer_id: e.target.value })}
                margin="normal"
                required
                placeholder="VD: ENG-001"
              />

              <TextField
                fullWidth
                label="Họ tên Kỹ sư"
                value={overrideForm.engineer_name}
                onChange={(e) => setOverrideForm({ ...overrideForm, engineer_name: e.target.value })}
                margin="normal"
                required
              />

              <TextField
                fullWidth
                label="Lý do Override"
                value={overrideForm.reason}
                onChange={(e) => setOverrideForm({ ...overrideForm, reason: e.target.value })}
                margin="normal"
                required
                multiline
                rows={4}
                placeholder="Giải thích chi tiết lý do override (tối thiểu 50 ký tự)"
                helperText={`${overrideForm.reason.length}/50 ký tự (tối thiểu)`}
                error={overrideForm.reason.length > 0 && overrideForm.reason.length < 50}
              />

              <TextField
                fullWidth
                label="Tài liệu tham chiếu (tùy chọn)"
                value={overrideForm.reference_doc}
                onChange={(e) => setOverrideForm({ ...overrideForm, reference_doc: e.target.value })}
                margin="normal"
                placeholder="VD: Công văn số 123/ABC ngày 01/01/2024"
              />
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseOverride}>Hủy</Button>
          <Button
            onClick={handleOverrideSubmit}
            variant="contained"
            color="warning"
            disabled={
              submitting ||
              overrideForm.reason.length < 50 ||
              !overrideForm.engineer_id ||
              !overrideForm.engineer_name
            }
          >
            {submitting ? <LinearProgress sx={{ width: 100 }} /> : 'Xác nhận Override'}
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default SafetyViolations;
