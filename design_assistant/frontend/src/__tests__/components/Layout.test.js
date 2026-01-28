/**
 * Layout Component Tests
 * Test sidebar navigation và layout rendering
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Layout from '../../components/Layout';

const theme = createTheme();

const renderWithProviders = (component, { route = '/' } = {}) => {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    </MemoryRouter>
  );
};

describe('Layout Component', () => {
  test('renders sidebar with brand name', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    // Use getAllByText since brand appears multiple times (responsive UI)
    const brandElements = screen.getAllByText(/HydroDraft/i);
    expect(brandElements.length).toBeGreaterThan(0);
  });

  test('renders children content', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  test('renders all menu sections', () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    );
    
    // Use getAllByText since sections appear multiple times (responsive UI)
    expect(screen.getAllByText('THIẾT KẾ').length).toBeGreaterThan(0);
    expect(screen.getAllByText('XUẤT BẢN').length).toBeGreaterThan(0);
    expect(screen.getAllByText('QUẢN LÝ').length).toBeGreaterThan(0);
  });

  test('renders Pro badge', () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    );
    
    const proBadges = screen.getAllByText('Pro');
    expect(proBadges.length).toBeGreaterThan(0);
  });

  test('highlights active menu item based on route', () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>,
      { route: '/design/tank' }
    );
    
    const tankMenuItems = screen.getAllByText('Thiết kế Bể');
    // At least one should be selected
    const selectedItems = tankMenuItems.filter(el => 
      el.closest('div[role="button"]')?.classList.contains('Mui-selected')
    );
    expect(selectedItems.length).toBeGreaterThan(0);
  });

  test('renders New badges on new features', () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    );
    
    const newBadges = screen.getAllByText('New');
    expect(newBadges.length).toBeGreaterThan(0);
  });
});
