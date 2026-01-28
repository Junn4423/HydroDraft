/**
 * CADValidation Component
 * Hiển thị kết quả validation bản vẽ CAD (Sprint 3)
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Divider,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  CheckCircle as OKIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  Straighten as DimensionIcon,
  TextFields as TextIcon,
  Layers as LayerIcon,
  GridOn as GridIcon,
  Place as PlaceIcon,
  TipsAndUpdates as TipsIcon,
} from '@mui/icons-material';

const CADValidation = ({ validation }) => {
  if (!validation) {
    return (
      <Alert severity="info">
        Chưa có dữ liệu validation. Vui lòng tạo bản vẽ trước.
      </Alert>
    );
  }

  const {
    is_valid,
    can_export,
    total_issues,
    issues_by_severity = {},
    issues_by_category = {},
    issues = [],
  } = validation;

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'error': return <ErrorIcon color="error" />;
      case 'warning': return <WarningIcon color="warning" />;
      case 'info': return <InfoIcon color="info" />;
      default: return <OKIcon color="success" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'error': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'info';
      default: return 'success';
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'dimension':
      case 'dimensions': return <DimensionIcon />;
      case 'text':
      case 'annotation': return <TextIcon />;
      case 'layer':
      case 'layers': return <LayerIcon />;
      case 'scale':
      case 'grid': return <GridIcon />;
      default: return <InfoIcon />;
    }
  };

  const errorCount = issues_by_severity.error || 0;
  const warningCount = issues_by_severity.warning || 0;
  const infoCount = issues_by_severity.info || 0;

  return (
    <Paper elevation={0} sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 2 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        {is_valid ? (
          <OKIcon color="success" sx={{ mr: 1, fontSize: 28 }} />
        ) : (
          <ErrorIcon color="error" sx={{ mr: 1, fontSize: 28 }} />
        )}
        <Typography variant="h6">Kiểm tra Bản vẽ CAD</Typography>
        <Chip
          size="small"
          label={can_export ? 'Có thể xuất' : 'Không thể xuất'}
          color={can_export ? 'success' : 'error'}
          sx={{ ml: 'auto' }}
        />
      </Box>

      {/* Summary */}
      <Alert severity={is_valid ? 'success' : 'error'} sx={{ mb: 2 }}>
        {is_valid ? (
          <>
            <strong>Bản vẽ hợp lệ!</strong> Đã kiểm tra các tiêu chuẩn CAD cơ bản.
          </>
        ) : (
          <>
            <strong>Phát hiện {total_issues} vấn đề.</strong> Vui lòng xem chi tiết bên dưới.
          </>
        )}
      </Alert>

      {/* Issue counts by severity */}
      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
        <Chip
          icon={<ErrorIcon />}
          label={`${errorCount} Lỗi`}
          color="error"
          variant={errorCount > 0 ? 'filled' : 'outlined'}
          size="small"
        />
        <Chip
          icon={<WarningIcon />}
          label={`${warningCount} Cảnh báo`}
          color="warning"
          variant={warningCount > 0 ? 'filled' : 'outlined'}
          size="small"
        />
        <Chip
          icon={<InfoIcon />}
          label={`${infoCount} Gợi ý`}
          color="info"
          variant={infoCount > 0 ? 'filled' : 'outlined'}
          size="small"
        />
      </Box>

      {/* Issues by category */}
      {Object.keys(issues_by_category).length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Theo danh mục:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {Object.entries(issues_by_category).map(([category, count]) => (
              <Chip
                key={category}
                icon={getCategoryIcon(category)}
                label={`${category}: ${count}`}
                size="small"
                variant="outlined"
              />
            ))}
          </Box>
        </Box>
      )}

      <Divider sx={{ my: 2 }} />

      {/* Detailed Issues */}
      {issues.length > 0 ? (
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Chi tiết vấn đề:
          </Typography>
          
          {/* Group issues by category */}
          {Object.entries(
            issues.reduce((acc, issue) => {
              const cat = issue.category || 'other';
              if (!acc[cat]) acc[cat] = [];
              acc[cat].push(issue);
              return acc;
            }, {})
          ).map(([category, categoryIssues]) => (
            <Accordion key={category} defaultExpanded={category === 'error'}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {getCategoryIcon(category)}
                  <Typography>{category.charAt(0).toUpperCase() + category.slice(1)}</Typography>
                  <Chip size="small" label={categoryIssues.length} />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <List dense>
                  {categoryIssues.map((issue, idx) => (
                    <ListItem key={idx}>
                      <ListItemIcon>
                        {getSeverityIcon(issue.severity)}
                      </ListItemIcon>
                      <ListItemText
                        primary={issue.message || issue.description}
                        secondary={
                          <>
                            {issue.location && <span><PlaceIcon sx={{ fontSize: 12, mr: 0.5, verticalAlign: 'middle' }} />{issue.location} | </span>}
                            {issue.suggestion && <span><TipsIcon sx={{ fontSize: 12, mr: 0.5, verticalAlign: 'middle' }} />{issue.suggestion}</span>}
                          </>
                        }
                      />
                      <Chip
                        size="small"
                        label={issue.severity}
                        color={getSeverityColor(issue.severity)}
                      />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      ) : (
        <Alert severity="success" icon={<OKIcon />}>
          Không phát hiện vấn đề nào. Bản vẽ đạt tiêu chuẩn.
        </Alert>
      )}

      {/* CAD Standards Info */}
      <Alert severity="info" sx={{ mt: 2 }} icon={<InfoIcon />}>
        <Typography variant="body2">
          <strong>Tiêu chuẩn kiểm tra:</strong> Layer naming (TCVN), DimStyles, TextStyles, 
          Scale consistency, Missing dimensions, Missing annotations.
        </Typography>
      </Alert>
    </Paper>
  );
};

export default CADValidation;
