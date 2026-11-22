import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import PatientCard from '../components/PatientCard';

const mockPatient = {
  id: 1,
  first_name: 'John',
  last_name: 'Doe',
  patient_code: 'PAT-2026-001',
  active_bed: {
    bed_number: 'ICU-01',
  },
};

const mockVital = {
  heart_rate: 76.0,
  spo2: 98.5,
  respiratory_rate: 16.0,
  temperature: 37.1,
};

describe('PatientCard Component', () => {
  it('renders patient name, code, and bed number', () => {
    render(
      <PatientCard
        patient={mockPatient}
        onSelect={() => {}}
        onToggleStream={() => {}}
      />
    );
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('PAT-2026-001')).toBeInTheDocument();
    expect(screen.getByText('ICU-01')).toBeInTheDocument();
  });

  it('renders all key physiological vitals', () => {
    render(
      <PatientCard
        patient={mockPatient}
        liveVital={mockVital}
        onSelect={() => {}}
        onToggleStream={() => {}}
      />
    );
    expect(screen.getByText(/76.0/)).toBeInTheDocument();
    expect(screen.getByText(/98.5/)).toBeInTheDocument();
    expect(screen.getByText(/16.0/)).toBeInTheDocument();
    expect(screen.getByText(/37.1/)).toBeInTheDocument();
  });

  it('displays streaming badge when isStreaming is true', () => {
    render(
      <PatientCard
        patient={mockPatient}
        isStreaming={true}
        onSelect={() => {}}
        onToggleStream={() => {}}
      />
    );
    expect(screen.getByText('Streaming')).toBeInTheDocument();
    expect(screen.getByText('Live Telemetry Active')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Stop/i })).toBeInTheDocument();
  });

  it('calls onSelect when patient card is clicked', () => {
    const onSelect = vi.fn();
    render(
      <PatientCard
        patient={mockPatient}
        onSelect={onSelect}
        onToggleStream={() => {}}
      />
    );
    fireEvent.click(screen.getByText('John Doe'));
    expect(onSelect).toHaveBeenCalledWith(1);
  });
});
