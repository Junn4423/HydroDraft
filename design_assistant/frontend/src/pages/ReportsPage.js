/**
 * Reports Page
 * Tạo báo cáo PDF kỹ thuật (Sprint 4)
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
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Description as ReportIcon,
  CheckCircle as CheckIcon,
  Article as ArticleIcon,
  Calculate as CalcIcon,
  TableChart as TableIcon,
  Image as ImageIcon,
  FileCopy as FileIcon,
  ListAlt as ListAltIcon,
} from '@mui/icons-material';
import ReportGenerator from '../components/ReportGenerator';

const ReportsPage = () => {
  const [activeTab, setActiveTab] = useState(0);

  // Sample data for demo
  const sampleDesignData = {
    project_name: 'Trạm XLNT Thành phố XYZ',
    tank_type: 'sedimentation',
    dimensions: {
      length: 12,
      width: 6,
      depth: 3.5,
    },
    hydraulic_results: {
      volume: { total: 252 },
      retention_time: 2.5,
    },
  };

  const sampleCalculationLog = {
    steps: [
      {
        description: 'Tính toán thể tích bể',
        formula: 'V = L × W × H',
        inputs: { L: 12, W: 6, H: 3.5 },
        result: 252,
        reference: 'TCVN 7957:2008',
      },
      {
        description: 'Kiểm tra thời gian lưu',
        formula: 'HRT = V / Q',
        inputs: { V: 252, Q: 100 },
        result: 2.52,
        reference: 'TCVN 7957:2008 - Bảng 5.1',
      },
    ],
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <ReportIcon color="primary" sx={{ fontSize: 40, mr: 2 }} />
        <Box>
          <Typography variant="h4">Báo cáo Kỹ thuật</Typography>
          <Typography variant="body2" color="text.secondary">
            Tạo báo cáo PDF chuyên nghiệp để nộp cơ quan thẩm định
          </Typography>
        </Box>
        <Chip label="Sprint 4" color="secondary" sx={{ ml: 'auto' }} />
      </Box>

      <Alert severity="success" sx={{ mb: 3 }}>
        <Typography variant="body2">
          Báo cáo được tạo tự động từ dữ liệu thiết kế, bao gồm thuyết minh, tính toán và danh mục bản vẽ.
          Phù hợp nộp Sở TN&MT, Sở Xây dựng.
        </Typography>
      </Alert>

      <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ mb: 3 }}>
        <Tab label="Tạo Báo cáo" />
        <Tab label="Cấu trúc" />
        <Tab label="Templates" />
      </Tabs>

      {activeTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={7}>
            <ReportGenerator 
              designData={sampleDesignData}
              calculationLog={sampleCalculationLog}
            />
          </Grid>
          <Grid item xs={12} md={5}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <FileIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Loại báo cáo</Typography>
                </Box>

                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Báo cáo Kỹ thuật
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemIcon><CheckIcon color="success" fontSize="small" /></ListItemIcon>
                      <ListItemText primary="Thuyết minh thiết kế" />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><CheckIcon color="success" fontSize="small" /></ListItemIcon>
                      <ListItemText primary="Bảng thông số kỹ thuật" />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><CheckIcon color="success" fontSize="small" /></ListItemIcon>
                      <ListItemText primary="Kết quả tính toán" />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><CheckIcon color="success" fontSize="small" /></ListItemIcon>
                      <ListItemText primary="Danh mục bản vẽ" />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><CheckIcon color="success" fontSize="small" /></ListItemIcon>
                      <ListItemText primary="Khung tên chuẩn" />
                    </ListItem>
                  </List>
                </Box>

                <Box>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Phụ lục Tính toán
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemIcon><CalcIcon color="info" fontSize="small" /></ListItemIcon>
                      <ListItemText primary="Công thức chi tiết" />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><TableIcon color="info" fontSize="small" /></ListItemIcon>
                      <ListItemText primary="Bảng thông số đầu vào" />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><ArticleIcon color="info" fontSize="small" /></ListItemIcon>
                      <ListItemText primary="Tham chiếu tiêu chuẩn" />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><CheckIcon color="info" fontSize="small" /></ListItemIcon>
                      <ListItemText primary="Kiểm tra điều kiện" />
                    </ListItem>
                  </List>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {activeTab === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <ListAltIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Cấu trúc Báo cáo Kỹ thuật</Typography>
                </Box>
                <List>
                  <ListItem>
                    <ListItemText 
                      primary="1. GIỚI THIỆU CHUNG" 
                      secondary="Tên dự án, chủ đầu tư, địa điểm, căn cứ pháp lý"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="2. SỐ LIỆU ĐẦU VÀO" 
                      secondary="Lưu lượng, chất lượng nước, tiêu chuẩn áp dụng"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="3. PHƯƠNG ÁN THIẾT KẾ" 
                      secondary="Lựa chọn công nghệ, dây chuyền xử lý"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="4. TÍNH TOÁN THIẾT KẾ" 
                      secondary="Chi tiết từng hạng mục công trình"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="5. KẾT CẤU CÔNG TRÌNH" 
                      secondary="Bê tông, cốt thép, vật liệu"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="6. DỰ TOÁN KHỐI LƯỢNG" 
                      secondary="Bê tông, thép, ván khuôn"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="7. DANH MỤC BẢN VẼ" 
                      secondary="List các bản vẽ kèm theo"
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📐 Cấu trúc Phụ lục Tính toán
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText 
                      primary="A. TÍNH TOÁN THỦY LỰC" 
                      secondary="Lưu lượng, vận tốc, tải trọng bề mặt"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="B. KÍCH THƯỚC CÔNG TRÌNH" 
                      secondary="Chiều dài, rộng, sâu"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="C. TÍNH TOÁN KẾT CẤU" 
                      secondary="Thành bể, đáy bể, nắp"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="D. BỐ TRÍ CỐT THÉP" 
                      secondary="Thép chính, thép phân bố"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="E. KIỂM TRA ỔN ĐỊNH" 
                      secondary="Chống đẩy nổi, ổn định trượt"
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {activeTab === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Alert severity="info">
              Templates báo cáo được xây dựng theo mẫu của các Sở TN&MT, Sở Xây dựng.
              Có thể tùy chỉnh theo yêu cầu cụ thể của từng địa phương.
            </Alert>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📝 Template Cơ bản
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Báo cáo đơn giản cho các công trình nhỏ, không yêu cầu thẩm định phức tạp.
                </Typography>
                <Chip label="5-10 trang" size="small" sx={{ mt: 1 }} />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card variant="outlined" sx={{ border: '2px solid', borderColor: 'primary.main' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📑 Template Đầy đủ
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Báo cáo chi tiết cho các dự án lớn, đáp ứng yêu cầu thẩm định của Sở TN&MT.
                </Typography>
                <Chip label="20-50 trang" size="small" color="primary" sx={{ mt: 1 }} />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📚 Template Nghiên cứu
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Báo cáo khoa học với đầy đủ tham khảo, phương pháp nghiên cứu.
                </Typography>
                <Chip label="50+ trang" size="small" sx={{ mt: 1 }} />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Container>
  );
};

export default ReportsPage;
