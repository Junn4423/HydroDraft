/**
 * BIM Export Page
 * Xuất BIM data cho Revit/IFC (Sprint 4)
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
} from '@mui/material';
import {
  Architecture as BIMIcon,
  Inventory as InventoryIcon,
  Build as BuildIcon,
  Code as CodeIcon,
} from '@mui/icons-material';
import BIMExport from '../components/BIMExport';
import IFCViewer from '../components/IFCViewer';

const BIMPage = () => {
  const [activeTab, setActiveTab] = useState(0);

  // Sample design data for demo
  const sampleDesignData = {
    tank_name: 'BL-01',
    tank_type: 'sedimentation',
    dimensions: {
      length: 12,
      width: 6,
      depth: 3.5,
      total_depth: 4.2,
      wall_thickness: 0.3,
      bottom_thickness: 0.4,
    },
    hydraulic_results: {
      volume: { total: 252, per_tank: 252 },
      retention_time: 2.5,
      surface_loading: 35,
    },
  };

  const sampleProjectInfo = {
    project_name: 'Trạm XLNT Thành phố XYZ',
    project_code: 'XLNT-2024-001',
    client: 'Ban QLDA Hạ tầng',
    location: 'Quận ABC, TP XYZ',
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <BIMIcon color="primary" sx={{ fontSize: 40, mr: 2 }} />
        <Box>
          <Typography variant="h4">BIM Export</Typography>
          <Typography variant="body2" color="text.secondary">
            Xuất dữ liệu BIM tương thích với Autodesk Revit thông qua Dynamo hoặc pyRevit
          </Typography>
        </Box>
        <Chip label="Sprint 4" color="secondary" sx={{ ml: 'auto' }} />
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>BIM Bridge</strong> - Tạo các file JSON data, Dynamo script (.dyn) và pyRevit script (.py) 
          để import geometry và parameters vào Revit dưới dạng native objects có thể chỉnh sửa.
        </Typography>
      </Alert>

      <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ mb: 3 }}>
        <Tab label="Export BIM" />
        <Tab label="3D Preview" />
        <Tab label="Hướng dẫn" />
      </Tabs>

      {activeTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <BIMExport 
              designData={sampleDesignData}
              projectInfo={sampleProjectInfo}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <InventoryIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">
                    Các file BIM được tạo
                  </Typography>
                </Box>
                
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" color="primary">BIM_Data.json</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Chứa geometry (vertices, faces), parameters (kích thước, vật liệu), 
                    và metadata (project info, element IDs).
                  </Typography>
                </Box>

                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" color="primary">Dynamo Script (.dyn)</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Visual programming script đọc JSON và tạo Family Instances trong Revit.
                    Hỗ trợ các loại: Tanks, Pipes, Manholes.
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="subtitle2" color="primary">pyRevit Script (.py)</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Python script sử dụng Revit API để tạo đối tượng. 
                    Phù hợp cho automation và batch processing.
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {activeTab === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <IFCViewer />
          </Grid>
        </Grid>
      )}

      {activeTab === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <BuildIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">
                    Cài đặt Dynamo
                  </Typography>
                </Box>
                <ol>
                  <li>Mở Revit 2020 trở lên</li>
                  <li>Tab Manage → Dynamo</li>
                  <li>File → Open → Chọn file .dyn đã tải</li>
                  <li>Cập nhật đường dẫn file JSON trong node "File Path"</li>
                  <li>Click "Run" để tạo đối tượng</li>
                </ol>

                <Alert severity="warning" sx={{ mt: 2 }}>
                  Cần cài đặt package "Data-Shapes" trong Dynamo Package Manager.
                </Alert>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CodeIcon sx={{ mr: 1, color: 'success.main' }} />
                  <Typography variant="h6">
                    Cài đặt pyRevit
                  </Typography>
                </Box>
                <ol>
                  <li>Tải pyRevit từ <a href="https://github.com/eirannejad/pyRevit" target="_blank" rel="noreferrer">GitHub</a></li>
                  <li>Cài đặt theo hướng dẫn</li>
                  <li>Copy file .py vào thư mục pyRevit extension</li>
                  <li>Restart Revit</li>
                  <li>Chạy script từ pyRevit tab</li>
                </ol>

                <Alert severity="info" sx={{ mt: 2 }}>
                  pyRevit hỗ trợ Revit 2017-2024. Kiểm tra version tương thích.
                </Alert>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Container>
  );
};

export default BIMPage;
