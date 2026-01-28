import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Alert,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  Chip,
  Button,
  IconButton,
  CircularProgress,
  TextField,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Folder as FolderIcon,
  Pool as PoolIcon,
  Timeline as TimelineIcon,
  Opacity as OpacityIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Storage as StorageIcon,
  Inventory as InventoryIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function ProjectsPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [dbStatus, setDbStatus] = useState(null);
  
  // Local storage data
  const [tankDesigns, setTankDesigns] = useState([]);
  const [pipelineDesigns, setPipelineDesigns] = useState([]);
  const [wellDesigns, setWellDesigns] = useState([]);
  
  // Database projects (if connected)
  const [dbProjects, setDbProjects] = useState([]);
  
  // Delete confirmation dialog
  const [deleteDialog, setDeleteDialog] = useState({ open: false, type: '', id: '' });

  // Load from localStorage
  useEffect(() => {
    loadLocalData();
    checkDatabaseStatus();
  }, []);

  const loadLocalData = () => {
    const tanks = JSON.parse(localStorage.getItem('recentTankDesigns') || '[]');
    const pipelines = JSON.parse(localStorage.getItem('recentPipelineDesigns') || '[]');
    const wells = JSON.parse(localStorage.getItem('recentWellDesigns') || '[]');
    
    setTankDesigns(tanks);
    setPipelineDesigns(pipelines);
    setWellDesigns(wells);
  };

  const checkDatabaseStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/health`, { timeout: 3000 });
      setDbStatus(response.data);
    } catch (err) {
      setDbStatus({ database: false, error: err.message });
    }
  };

  const loadDbProjects = async () => {
    setLoading(true);
    try {
      // Try to load projects from database
      const response = await axios.get(`${API_URL}/api/v1/projects/`);
      setDbProjects(response.data || []);
    } catch (err) {
      console.log('Projects API not available:', err.message);
      setDbProjects([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteLocal = (type, id) => {
    if (type === 'tank') {
      const updated = tankDesigns.filter(d => d.id !== id);
      setTankDesigns(updated);
      localStorage.setItem('recentTankDesigns', JSON.stringify(updated));
    } else if (type === 'pipeline') {
      const updated = pipelineDesigns.filter(d => d.id !== id);
      setPipelineDesigns(updated);
      localStorage.setItem('recentPipelineDesigns', JSON.stringify(updated));
    } else if (type === 'well') {
      const updated = wellDesigns.filter(d => d.id !== id);
      setWellDesigns(updated);
      localStorage.setItem('recentWellDesigns', JSON.stringify(updated));
    }
    setDeleteDialog({ open: false, type: '', id: '' });
  };

  const handleClearAll = () => {
    localStorage.removeItem('recentTankDesigns');
    localStorage.removeItem('recentPipelineDesigns');
    localStorage.removeItem('recentWellDesigns');
    loadLocalData();
  };

  const getAllDesigns = () => {
    return [
      ...tankDesigns.map(d => ({ ...d, designType: 'tank' })),
      ...pipelineDesigns.map(d => ({ ...d, designType: 'pipeline' })),
      ...wellDesigns.map(d => ({ ...d, designType: 'well' })),
    ].sort((a, b) => new Date(b.date) - new Date(a.date));
  };

  const getFilteredDesigns = () => {
    const all = getAllDesigns();
    if (!searchTerm) return all;
    return all.filter(d => 
      d.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.type?.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const getDesignIcon = (type) => {
    switch(type) {
      case 'tank': return <PoolIcon color="primary" />;
      case 'pipeline': return <TimelineIcon color="success" />;
      case 'well': return <OpacityIcon color="warning" />;
      default: return <FolderIcon />;
    }
  };

  const getDesignTypeLabel = (type) => {
    switch(type) {
      case 'tank': return 'Bể';
      case 'pipeline': return 'Đường ống';
      case 'well': return 'Giếng';
      default: return type;
    }
  };

  const totalDesigns = tankDesigns.length + pipelineDesigns.length + wellDesigns.length;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <FolderIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h5">Quản lý Dự án</Typography>
        </Box>
        <Box>
          <Chip
            icon={<StorageIcon />}
            label={dbStatus?.database ? 'DB Connected' : 'Local Storage'}
            color={dbStatus?.database ? 'success' : 'default'}
            variant="outlined"
            sx={{ mr: 1 }}
          />
          <IconButton onClick={() => { loadLocalData(); checkDatabaseStatus(); }} title="Refresh">
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light', color: 'white' }}>
            <Typography variant="h4">{totalDesigns}</Typography>
            <Typography variant="body2">Tổng thiết kế</Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light', color: 'white' }}>
            <Typography variant="h4">{tankDesigns.length}</Typography>
            <Typography variant="body2">Thiết kế bể</Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'white' }}>
            <Typography variant="h4">{pipelineDesigns.length}</Typography>
            <Typography variant="body2">Tuyến ống</Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light', color: 'white' }}>
            <Typography variant="h4">{wellDesigns.length}</Typography>
            <Typography variant="body2">Giếng</Typography>
          </Paper>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ mb: 2 }}>
            <Tab label={`Tất cả (${totalDesigns})`} />
            <Tab label={`Bể (${tankDesigns.length})`} />
            <Tab label={`Đường ống (${pipelineDesigns.length})`} />
            <Tab label={`Giếng (${wellDesigns.length})`} />
          </Tabs>

          {/* Search Bar */}
          <TextField
            fullWidth
            size="small"
            placeholder="Tìm kiếm theo tên hoặc loại..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ mb: 2 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              {/* All Designs Tab */}
              {activeTab === 0 && (
                getFilteredDesigns().length === 0 ? (
                  <Alert severity="info">
                    Chưa có thiết kế nào. Hãy tạo thiết kế mới từ các trang Thiết kế Bể, Đường ống hoặc Giếng.
                  </Alert>
                ) : (
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Loại</TableCell>
                          <TableCell>Tên</TableCell>
                          <TableCell>Chi tiết</TableCell>
                          <TableCell>Ngày tạo</TableCell>
                          <TableCell align="center">Thao tác</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {getFilteredDesigns().map((design) => (
                          <TableRow key={`${design.designType}-${design.id}`} hover>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {getDesignIcon(design.designType)}
                                <Chip 
                                  label={getDesignTypeLabel(design.designType)} 
                                  size="small"
                                  variant="outlined"
                                />
                              </Box>
                            </TableCell>
                            <TableCell><strong>{design.name}</strong></TableCell>
                            <TableCell>
                              {design.designType === 'tank' && design.dimensions && (
                                `${design.dimensions.length}x${design.dimensions.width}m`
                              )}
                              {design.designType === 'pipeline' && design.total_length && (
                                `${design.total_length}m`
                              )}
                              {design.designType === 'well' && design.depth && (
                                `${design.depth}m`
                              )}
                            </TableCell>
                            <TableCell>
                              {new Date(design.date).toLocaleDateString('vi-VN', {
                                day: '2-digit',
                                month: '2-digit',
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </TableCell>
                            <TableCell align="center">
                              <IconButton 
                                size="small" 
                                color="primary"
                                href={`${API_URL}/api/v1/export/download/${design.id}`}
                                target="_blank"
                                title="Tải bản vẽ"
                              >
                                <DownloadIcon fontSize="small" />
                              </IconButton>
                              <IconButton 
                                size="small" 
                                color="error"
                                onClick={() => setDeleteDialog({ 
                                  open: true, 
                                  type: design.designType, 
                                  id: design.id 
                                })}
                                title="Xóa"
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )
              )}

              {/* Tank Designs Tab */}
              {activeTab === 1 && (
                tankDesigns.length === 0 ? (
                  <Alert severity="info">Chưa có thiết kế bể nào.</Alert>
                ) : (
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Ký hiệu</TableCell>
                          <TableCell>Loại bể</TableCell>
                          <TableCell>Kích thước (LxW)</TableCell>
                          <TableCell>Ngày tạo</TableCell>
                          <TableCell align="center">Thao tác</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {tankDesigns.map((design) => (
                          <TableRow key={design.id} hover>
                            <TableCell><strong>{design.name}</strong></TableCell>
                            <TableCell>
                              <Chip label={design.type} size="small" variant="outlined" />
                            </TableCell>
                            <TableCell>
                              {design.dimensions?.length}m x {design.dimensions?.width}m
                            </TableCell>
                            <TableCell>
                              {new Date(design.date).toLocaleDateString('vi-VN')}
                            </TableCell>
                            <TableCell align="center">
                              <IconButton 
                                size="small" 
                                color="error"
                                onClick={() => setDeleteDialog({ open: true, type: 'tank', id: design.id })}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )
              )}

              {/* Pipeline Designs Tab */}
              {activeTab === 2 && (
                pipelineDesigns.length === 0 ? (
                  <Alert severity="info">Chưa có thiết kế đường ống nào.</Alert>
                ) : (
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Ký hiệu</TableCell>
                          <TableCell>Loại ống</TableCell>
                          <TableCell>Chiều dài</TableCell>
                          <TableCell>Ngày tạo</TableCell>
                          <TableCell align="center">Thao tác</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {pipelineDesigns.map((design) => (
                          <TableRow key={design.id} hover>
                            <TableCell><strong>{design.name}</strong></TableCell>
                            <TableCell>
                              <Chip label={design.type} size="small" variant="outlined" />
                            </TableCell>
                            <TableCell>{design.total_length} m</TableCell>
                            <TableCell>
                              {new Date(design.date).toLocaleDateString('vi-VN')}
                            </TableCell>
                            <TableCell align="center">
                              <IconButton 
                                size="small" 
                                color="error"
                                onClick={() => setDeleteDialog({ open: true, type: 'pipeline', id: design.id })}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )
              )}

              {/* Well Designs Tab */}
              {activeTab === 3 && (
                wellDesigns.length === 0 ? (
                  <Alert severity="info">Chưa có thiết kế giếng nào.</Alert>
                ) : (
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Ký hiệu</TableCell>
                          <TableCell>Loại</TableCell>
                          <TableCell>Chiều sâu</TableCell>
                          <TableCell>Ngày tạo</TableCell>
                          <TableCell align="center">Thao tác</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {wellDesigns.map((design) => (
                          <TableRow key={design.id} hover>
                            <TableCell><strong>{design.name}</strong></TableCell>
                            <TableCell>
                              <Chip label={design.type} size="small" variant="outlined" />
                            </TableCell>
                            <TableCell>{design.depth} m</TableCell>
                            <TableCell>
                              {new Date(design.date).toLocaleDateString('vi-VN')}
                            </TableCell>
                            <TableCell align="center">
                              <IconButton 
                                size="small" 
                                color="error"
                                onClick={() => setDeleteDialog({ open: true, type: 'well', id: design.id })}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )
              )}
            </>
          )}

          {/* Clear All Button */}
          {totalDesigns > 0 && (
            <Box sx={{ mt: 2, textAlign: 'right' }}>
              <Button 
                variant="outlined" 
                color="error" 
                size="small"
                onClick={handleClearAll}
              >
                Xóa tất cả lịch sử
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Database Status Info */}
      <Paper sx={{ p: 2, mt: 2, bgcolor: 'grey.50' }}>
        <Typography variant="subtitle2" gutterBottom>
          <StorageIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
          Trạng thái lưu trữ
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {dbStatus?.database ? (
            <>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CheckCircleIcon color="success" sx={{ mr: 1 }} />
                Database MySQL đã kết nối
              </Box>
              • Dữ liệu được lưu vào database và có thể truy cập từ nhiều thiết bị<br />
              • Đồng bộ với local storage để đảm bảo tính liên tục
            </>
          ) : (
            <>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <InventoryIcon sx={{ mr: 1 }} />
                Đang sử dụng Local Storage
              </Box>
              • Dữ liệu được lưu trên trình duyệt của bạn<br />
              • Sẽ mất khi xóa cache hoặc đổi trình duyệt<br />
              • Khởi động Laragon để kết nối MySQL
            </>
          )}
        </Typography>
      </Paper>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialog.open} onClose={() => setDeleteDialog({ open: false, type: '', id: '' })}>
        <DialogTitle>Xác nhận xóa</DialogTitle>
        <DialogContent>
          <Typography>Bạn có chắc muốn xóa thiết kế này khỏi lịch sử?</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog({ open: false, type: '', id: '' })}>
            Hủy
          </Button>
          <Button 
            color="error" 
            variant="contained"
            onClick={() => handleDeleteLocal(deleteDialog.type, deleteDialog.id)}
          >
            Xóa
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ProjectsPage;
