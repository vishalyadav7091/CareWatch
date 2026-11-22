import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import ConnectionStatus from '../components/ConnectionStatus';

describe('ConnectionStatus Component', () => {
  it('renders online state with active patient count', () => {
    render(<ConnectionStatus connected={true} livePatients={3} />);
    expect(screen.getByText('Live')).toBeInTheDocument();
    expect(screen.getByText(/3 streaming/i)).toBeInTheDocument();
  });

  it('renders offline/reconnecting state when disconnected', () => {
    render(<ConnectionStatus connected={false} error="Network disconnected" />);
    expect(screen.getByText('Backend offline')).toBeInTheDocument();
  });
});
