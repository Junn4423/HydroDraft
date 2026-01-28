/**
 * SystemStatus Component Tests
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import SystemStatus from '../../components/SystemStatus';
import { systemAPI } from '../../services/api';

jest.mock('../../services/api', () => ({
  systemAPI: {
    healthCheck: jest.fn()
  }
}));

const theme = createTheme();

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('SystemStatus Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders in compact mode', async () => {
    systemAPI.healthCheck.mockResolvedValueOnce({
      data: {
        status: 'ok',
        database: { status: 'ok' },
        version: '2.0.0'
      }
    });

    renderWithTheme(<SystemStatus compact />);
    
    await waitFor(() => {
      expect(screen.getByText('API')).toBeInTheDocument();
      expect(screen.getByText('DB')).toBeInTheDocument();
    });
  });

  test('renders in full mode with header', async () => {
    systemAPI.healthCheck.mockResolvedValueOnce({
      data: {
        status: 'ok',
        database: { status: 'ok' },
        version: '2.0.0'
      }
    });

    renderWithTheme(<SystemStatus />);
    
    await waitFor(() => {
      expect(screen.getByText(/Trạng thái Hệ thống/i)).toBeInTheDocument();
    });
  });

  test('shows API Server status', async () => {
    systemAPI.healthCheck.mockResolvedValueOnce({
      data: {
        status: 'ok',
        database: { status: 'ok' },
        version: '2.0.0'
      }
    });

    renderWithTheme(<SystemStatus />);
    
    await waitFor(() => {
      expect(screen.getByText('API Server')).toBeInTheDocument();
    });
  });

  test('shows Database status', async () => {
    systemAPI.healthCheck.mockResolvedValueOnce({
      data: {
        status: 'ok',
        database: { status: 'ok' },
        version: '2.0.0'
      }
    });

    renderWithTheme(<SystemStatus />);
    
    await waitFor(() => {
      expect(screen.getByText('SQLite Database')).toBeInTheDocument();
    });
  });

  test('handles API error gracefully', async () => {
    systemAPI.healthCheck.mockRejectedValueOnce(new Error('Connection failed'));

    renderWithTheme(<SystemStatus compact />);
    
    await waitFor(() => {
      expect(screen.getByText('API')).toBeInTheDocument();
    });
  });

  test('displays version when available', async () => {
    systemAPI.healthCheck.mockResolvedValueOnce({
      data: {
        status: 'ok',
        database: { status: 'ok' },
        version: '2.0.0'
      }
    });

    renderWithTheme(<SystemStatus compact />);
    
    await waitFor(() => {
      expect(screen.getByText('v2.0.0')).toBeInTheDocument();
    });
  });
});
