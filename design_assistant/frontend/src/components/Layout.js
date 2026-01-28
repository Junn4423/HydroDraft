import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Divider,
  useTheme,
  useMediaQuery,
  Chip,
  Collapse,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Home as HomeIcon,
  Pool as PoolIcon,
  Timeline as TimelineIcon,
  Opacity as OpacityIcon,
  Folder as FolderIcon,
  Settings as SettingsIcon,
  Architecture as BIMIcon,
  Description as ReportIcon,
  History as HistoryIcon,
  ViewInAr as ViewerIcon,
  ExpandLess,
  ExpandMore,
  Draw as CADIcon,
  Science as ScienceIcon,
  Water as WaterIcon,
} from '@mui/icons-material';
import SystemStatus from './SystemStatus';

const drawerWidth = 280;

const menuItems = [
  { text: 'Trang chủ', icon: <HomeIcon />, path: '/' },
  { divider: true, label: 'THIẾT KẾ' },
  { text: 'Thiết kế Bể', icon: <PoolIcon />, path: '/design/tank' },
  { text: 'Thiết kế Đường ống', icon: <TimelineIcon />, path: '/design/pipeline' },
  { text: 'Thiết kế Giếng', icon: <OpacityIcon />, path: '/design/well' },
  { divider: true, label: 'XUẤT BẢN' },
  { text: 'CAD Chuyên nghiệp', icon: <CADIcon />, path: '/cad', badge: 'New' },
  { text: 'BIM Export', icon: <BIMIcon />, path: '/bim', badge: 'New' },
  { text: 'Báo cáo PDF', icon: <ReportIcon />, path: '/reports', badge: 'New' },
  { divider: true, label: 'QUẢN LÝ' },
  { text: 'Dự án', icon: <FolderIcon />, path: '/projects' },
  { text: 'Lịch sử Phiên bản', icon: <HistoryIcon />, path: '/versions', badge: 'New' },
  { text: 'Trình xem 3D', icon: <ViewerIcon />, path: '/viewer', badge: 'New' },
  { divider: true },
  { text: 'Cài đặt', icon: <SettingsIcon />, path: '/settings' },
];

function Layout({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Toolbar sx={{ bgcolor: 'primary.dark' }}>
        <WaterIcon sx={{ mr: 1, color: 'white' }} />
        <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 'bold', color: 'white' }}>
          HydroDraft
        </Typography>
        <Chip size="small" label="Pro" color="warning" sx={{ ml: 1 }} />
      </Toolbar>
      <Divider />
      <Box sx={{ flexGrow: 1, overflowY: 'auto', overflowX: 'hidden' }}>
        <List>
          {menuItems.map((item, index) => (
            item.divider ? (
              <Box key={index}>
                <Divider sx={{ my: 1 }} />
                {item.label && (
                  <Typography variant="caption" color="text.secondary" sx={{ px: 2, py: 0.5, display: 'block' }}>
                    {item.label}
                  </Typography>
                )}
              </Box>
            ) : (
              <ListItem key={item.text} disablePadding>
                <ListItemButton
                  selected={location.pathname === item.path}
                  onClick={() => {
                    navigate(item.path);
                    if (isMobile) handleDrawerToggle();
                  }}
                >
                  <ListItemIcon sx={{ color: location.pathname === item.path ? 'primary.main' : 'inherit' }}>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText primary={item.text} />
                  {item.badge && (
                    <Chip size="small" label={item.badge} color="secondary" sx={{ height: 20, fontSize: 10 }} />
                  )}
                </ListItemButton>
              </ListItem>
            )
          ))}
        </List>
      </Box>
      
      {/* System Status at bottom - now part of flex layout */}
      <Box sx={{ p: 1, bgcolor: 'grey.100', borderTop: 1, borderColor: 'divider' }}>
        <SystemStatus compact />
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="mở menu"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            HydroDraft - Nền tảng Thiết kế Hạ tầng Môi trường
          </Typography>
          <Chip 
            label="Offline" 
            color="success" 
            size="small" 
            sx={{ mr: 1 }}
          />
        </Toolbar>
      </AppBar>
      
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        
        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          mt: '64px',
        }}
      >
        {children}
      </Box>
    </Box>
  );
}

export default Layout;
