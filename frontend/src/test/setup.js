import '@testing-library/jest-dom';

// ResizeObserver mock for Recharts
global.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
};
