/**
 * API Service Tests
 * Test các API calls và error handling
 */

// Mock axios before importing the API module
jest.mock('axios', () => {
  const mockAxiosInstance = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() }
    }
  };
  return {
    create: jest.fn(() => mockAxiosInstance),
    default: {
      create: jest.fn(() => mockAxiosInstance)
    }
  };
});

import axios from 'axios';
import { 
  systemAPI, 
  tankAPI, 
  cadAPI, 
  bimAPI, 
  versionAPI, 
  reportAPI 
} from '../../services/api';

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('systemAPI', () => {
    test('healthCheck function exists', () => {
      // The API module exports the function
      expect(typeof systemAPI.healthCheck).toBe('function');
    });
  });

  describe('tankAPI', () => {
    test('design function exists', () => {
      expect(typeof tankAPI.design).toBe('function');
    });

    test('calculate function exists', () => {
      expect(typeof tankAPI.calculate).toBe('function');
    });

    test('designV2 function exists', () => {
      expect(typeof tankAPI.designV2).toBe('function');
    });
  });

  describe('cadAPI', () => {
    test('createTankDrawing function exists', () => {
      expect(typeof cadAPI.createTankDrawing).toBe('function');
    });

    test('validateDrawing function exists', () => {
      expect(typeof cadAPI.validateDrawing).toBe('function');
    });

    test('getBlocks function exists', () => {
      expect(typeof cadAPI.getBlocks).toBe('function');
    });
  });

  describe('bimAPI', () => {
    test('exportTank function exists', () => {
      expect(typeof bimAPI.exportTank).toBe('function');
    });

    test('exportProject function exists', () => {
      expect(typeof bimAPI.exportProject).toBe('function');
    });

    test('downloadFile returns correct URL format', () => {
      const filename = 'test.json';
      const url = bimAPI.downloadFile(filename);
      expect(url).toContain('/api/v1/bim/download/');
      expect(url).toContain(filename);
    });
  });

  describe('versionAPI', () => {
    test('createVersion function exists', () => {
      expect(typeof versionAPI.createVersion).toBe('function');
    });

    test('listVersions function exists', () => {
      expect(typeof versionAPI.listVersions).toBe('function');
    });

    test('compareVersions function exists', () => {
      expect(typeof versionAPI.compareVersions).toBe('function');
    });
  });

  describe('reportAPI', () => {
    test('generateTechnicalReport function exists', () => {
      expect(typeof reportAPI.generateTechnicalReport).toBe('function');
    });

    test('downloadReport returns correct URL format', () => {
      const filename = 'report.pdf';
      const url = reportAPI.downloadReport(filename);
      expect(url).toContain('/api/v1/reports/download/');
      expect(url).toContain(filename);
    });
  });
});
