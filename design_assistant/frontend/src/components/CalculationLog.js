/**
 * CalculationLog Component
 * Hiển thị chi tiết các bước tính toán (Sprint 2)
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Chip,
  Alert,
  IconButton,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  ContentCopy as CopyIcon,
  BarChart as ResultIcon,
  MenuBook as ReferenceIcon,
} from '@mui/icons-material';

const CalculationLog = ({ logs, title = "Nhật ký Tính toán" }) => {
  const [expandedPanel, setExpandedPanel] = useState(false);

  if (!logs || logs.length === 0) {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        Chưa có dữ liệu tính toán. Vui lòng chạy thiết kế để xem chi tiết.
      </Alert>
    );
  }

  const handlePanelChange = (panel) => (event, isExpanded) => {
    setExpandedPanel(isExpanded ? panel : false);
  };

  const copyFormula = (formula) => {
    navigator.clipboard.writeText(formula);
  };

  const getStatusIcon = (conditions) => {
    if (!conditions) return <CheckIcon color="success" />;
    if (conditions.warnings?.length > 0) return <WarningIcon color="warning" />;
    if (conditions.errors?.length > 0) return <ErrorIcon color="error" />;
    return <CheckIcon color="success" />;
  };

  const getStatusChip = (conditions) => {
    if (!conditions) {
      return <Chip size="small" color="success" label="OK" />;
    }
    if (conditions.errors?.length > 0) {
      return <Chip size="small" color="error" label="Vi phạm" />;
    }
    if (conditions.warnings?.length > 0) {
      return <Chip size="small" color="warning" label="Cảnh báo" />;
    }
    return <Chip size="small" color="success" label="Đạt" />;
  };

  return (
    <Paper elevation={0} sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <InfoIcon color="primary" sx={{ mr: 1 }} />
        <Typography variant="h6">{title}</Typography>
        <Chip 
          size="small" 
          label={`${logs.length} bước`} 
          sx={{ ml: 'auto' }} 
          color="primary" 
          variant="outlined"
        />
      </Box>

      {logs.map((log, index) => (
        <Accordion
          key={index}
          expanded={expandedPanel === index}
          onChange={handlePanelChange(index)}
          sx={{ mb: 1, '&:before': { display: 'none' } }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{ bgcolor: 'white', borderRadius: 1 }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
              {getStatusIcon(log.conditions)}
              <Typography sx={{ ml: 1, fontWeight: 'medium' }}>
                {log.description || `Bước ${index + 1}`}
              </Typography>
              <Box sx={{ ml: 'auto', mr: 2 }}>
                {getStatusChip(log.conditions)}
              </Box>
            </Box>
          </AccordionSummary>
          
          <AccordionDetails sx={{ bgcolor: 'grey.100' }}>
            {/* Formula */}
            {log.formula_latex && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  📐 Công thức
                </Typography>
                <Paper 
                  sx={{ 
                    p: 2, 
                    bgcolor: '#1a1a2e', 
                    color: '#00d9ff',
                    fontFamily: 'monospace',
                    position: 'relative'
                  }}
                >
                  <code>{log.formula_latex}</code>
                  <Tooltip title="Sao chép công thức">
                    <IconButton
                      size="small"
                      sx={{ position: 'absolute', top: 4, right: 4, color: 'grey.400' }}
                      onClick={() => copyFormula(log.formula_latex)}
                    >
                      <CopyIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Paper>
              </Box>
            )}

            {/* Inputs */}
            {log.inputs && Object.keys(log.inputs).length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  📥 Thông số đầu vào
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      {Object.entries(log.inputs).map(([key, value]) => (
                        <TableRow key={key}>
                          <TableCell sx={{ fontWeight: 'medium', width: '40%' }}>
                            {key}
                          </TableCell>
                          <TableCell>
                            <code>{typeof value === 'object' ? JSON.stringify(value) : value}</code>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}

            {/* Result */}
            {log.result !== undefined && (
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <ResultIcon fontSize="small" sx={{ mr: 0.5, color: 'primary.main' }} />
                  <Typography variant="subtitle2" color="primary">Kết quả</Typography>
                </Box>
                <Paper sx={{ p: 2, bgcolor: 'success.light', color: 'success.contrastText' }}>
                  <Typography variant="h6">
                    {typeof log.result === 'object' 
                      ? JSON.stringify(log.result, null, 2) 
                      : log.result
                    }
                    {log.unit && <span style={{ fontSize: '0.8em', marginLeft: 8 }}>{log.unit}</span>}
                  </Typography>
                </Paper>
              </Box>
            )}

            {/* Reference */}
            {log.reference && (
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <ReferenceIcon fontSize="small" sx={{ mr: 0.5, color: 'primary.main' }} />
                  <Typography variant="subtitle2" color="primary">Tham chiếu</Typography>
                </Box>
                <Alert severity="info" icon={false}>
                  {log.reference}
                </Alert>
              </Box>
            )}

            {/* Conditions/Warnings */}
            {log.conditions && (
              <>
                {log.conditions.warnings?.map((warning, i) => (
                  <Alert key={i} severity="warning" sx={{ mb: 1 }}>
                    {warning}
                  </Alert>
                ))}
                {log.conditions.errors?.map((error, i) => (
                  <Alert key={i} severity="error" sx={{ mb: 1 }}>
                    {error}
                  </Alert>
                ))}
                {log.conditions.info?.map((info, i) => (
                  <Alert key={i} severity="info" sx={{ mb: 1 }}>
                    {info}
                  </Alert>
                ))}
              </>
            )}

            <Divider sx={{ my: 1 }} />
            
            {/* Timestamp */}
            <Typography variant="caption" color="text.secondary">
              Thực hiện lúc: {log.timestamp || new Date().toLocaleString('vi-VN')}
            </Typography>
          </AccordionDetails>
        </Accordion>
      ))}
    </Paper>
  );
};

export default CalculationLog;
