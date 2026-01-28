/**
 * App Component Tests
 * Test các route và rendering cơ bản
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import App from '../App';

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

describe('App Component', () => {
  test('renders without crashing', () => {
    renderWithProviders(<App />);
  });

  test('renders home page by default', async () => {
    renderWithProviders(<App />);
    
    await waitFor(() => {
      // Use getAllByText since text may appear multiple times
      const elements = screen.getAllByText(/HydroDraft/i);
      expect(elements.length).toBeGreaterThan(0);
    });
  });

  test('renders navigation menu', async () => {
    renderWithProviders(<App />);
    
    await waitFor(() => {
      // Use getAllByText for elements that may appear multiple times
      expect(screen.getAllByText(/Thiết kế Bể/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Thiết kế Đường ống/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Thiết kế Giếng/i).length).toBeGreaterThan(0);
    });
  });

  test('renders CAD menu item', async () => {
    renderWithProviders(<App />);
    
    await waitFor(() => {
      expect(screen.getAllByText(/CAD Chuyên nghiệp/i).length).toBeGreaterThan(0);
    });
  });

  test('renders BIM menu item', async () => {
    renderWithProviders(<App />);
    
    await waitFor(() => {
      expect(screen.getAllByText(/BIM Export/i).length).toBeGreaterThan(0);
    });
  });
});
