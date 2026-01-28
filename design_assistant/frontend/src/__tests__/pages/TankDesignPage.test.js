/**
 * TankDesignPage Tests
 * Test form inputs, validation và API calls
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import axios from 'axios';
import TankDesignPage from '../../pages/TankDesignPage';

jest.mock('axios');

const theme = createTheme();

const renderWithProviders = (component) => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('TankDesignPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('renders page header', () => {
    renderWithProviders(<TankDesignPage />);
    
    expect(screen.getByText(/Thiết kế Bể/i)).toBeInTheDocument();
  });

  test('renders form fields', () => {
    renderWithProviders(<TankDesignPage />);
    
    expect(screen.getByLabelText(/Tên dự án/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Ký hiệu bể/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Lưu lượng thiết kế/i)).toBeInTheDocument();
  });

  test('renders tank type selector', () => {
    renderWithProviders(<TankDesignPage />);
    
    // Select uses aria-labelledby, so we check for the label text using getAllByText
    const labels = screen.getAllByText(/Loại bể/i);
    expect(labels.length).toBeGreaterThan(0);
  });

  test('updates form values on input change', () => {
    renderWithProviders(<TankDesignPage />);
    
    const projectInput = screen.getByLabelText(/Tên dự án/i);
    fireEvent.change(projectInput, { target: { value: 'Test Project' } });
    
    expect(projectInput.value).toBe('Test Project');
  });

  test('submits form and shows loading state', async () => {
    const mockResponse = {
      data: {
        job_id: 'test-123',
        status: 'completed',
        dimensions: {
          length: 10,
          width: 5,
          depth: 3,
          total_depth: 4,
          number_of_tanks: 2
        },
        hydraulic_results: {
          volume: { total: 300, per_tank: 150 },
          retention_time: 2.5,
          surface_loading: 35
        }
      }
    };
    
    axios.post.mockResolvedValueOnce(mockResponse);
    
    renderWithProviders(<TankDesignPage />);
    
    const projectInput = screen.getByLabelText(/Tên dự án/i);
    const tankNameInput = screen.getByLabelText(/Ký hiệu bể/i);
    
    fireEvent.change(projectInput, { target: { value: 'Test Project' } });
    fireEvent.change(tankNameInput, { target: { value: 'BL-01' } });
    
    const submitButton = screen.getByRole('button', { name: /Thiết kế & Xuất bản vẽ/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(axios.post).toHaveBeenCalled();
    });
  });

  test('shows error message on API failure', async () => {
    axios.post.mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Validation error'
        }
      }
    });
    
    renderWithProviders(<TankDesignPage />);
    
    const projectInput = screen.getByLabelText(/Tên dự án/i);
    const tankNameInput = screen.getByLabelText(/Ký hiệu bể/i);
    
    fireEvent.change(projectInput, { target: { value: 'Test Project' } });
    fireEvent.change(tankNameInput, { target: { value: 'BL-01' } });
    
    const submitButton = screen.getByRole('button', { name: /Thiết kế & Xuất bản vẽ/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Validation error/i)).toBeInTheDocument();
    });
  });

  test('validates required fields', () => {
    renderWithProviders(<TankDesignPage />);
    
    const projectInput = screen.getByLabelText(/Tên dự án/i);
    const tankNameInput = screen.getByLabelText(/Ký hiệu bể/i);
    
    expect(projectInput).toBeRequired();
    expect(tankNameInput).toBeRequired();
  });

  test('renders tabs for input, result, and history', () => {
    renderWithProviders(<TankDesignPage />);
    
    expect(screen.getByRole('tab', { name: /Nhập liệu/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /Kết quả/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /Lịch sử/i })).toBeInTheDocument();
  });
});
