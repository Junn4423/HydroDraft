import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';

// Layout
import Layout from './components/Layout';

// Pages
import HomePage from './pages/HomePage';
import TankDesignPage from './pages/TankDesignPage';
import PipelineDesignPage from './pages/PipelineDesignPage';
import WellDesignPage from './pages/WellDesignPage';
import ProjectsPage from './pages/ProjectsPage';
import CADPage from './pages/CADPage';
import BIMPage from './pages/BIMPage';
import ReportsPage from './pages/ReportsPage';
import VersionsPage from './pages/VersionsPage';
import ViewerPage from './pages/ViewerPage';
import SettingsPage from './pages/SettingsPage';

function App() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          {/* Design */}
          <Route path="/design/tank" element={<TankDesignPage />} />
          <Route path="/design/pipeline" element={<PipelineDesignPage />} />
          <Route path="/design/well" element={<WellDesignPage />} />
          {/* Export - Sprint 3 & 4 */}
          <Route path="/cad" element={<CADPage />} />
          <Route path="/bim" element={<BIMPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          {/* Management - Sprint 4 */}
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/versions" element={<VersionsPage />} />
          <Route path="/viewer" element={<ViewerPage />} />
          {/* Settings */}
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Layout>
    </Box>
  );
}

export default App;
