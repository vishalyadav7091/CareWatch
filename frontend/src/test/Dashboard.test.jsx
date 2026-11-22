import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import React from 'react';
import Dashboard from '../components/Dashboard';
import * as apiModule from '../services/api';

describe('Dashboard Component', () => {
  const mockUser = { id: 1, full_name: 'Dr. Sarah Smith', role: 'doctor' };

  beforeEach(() => {
    vi.spyOn(apiModule.clinicalService, 'getPatients').mockResolvedValue({
      data: {
        success: true,
        data: [
          {
            id: 1,
            first_name: 'John',
            last_name: 'Doe',
            patient_code: 'PAT-2026-001',
            active_bed: { bed_number: 'ICU-01' },
          },
        ],
      },
    });
    vi.spyOn(apiModule.clinicalService, 'getBeds').mockResolvedValue({
      data: {
        success: true,
        data: [
          { id: 1, bed_number: 'ICU-01', status: 'occupied' },
          { id: 2, bed_number: 'ICU-02', status: 'available' },
        ],
      },
    });
    vi.spyOn(apiModule.clinicalService, 'getAlerts').mockResolvedValue({
      data: { success: true, data: [] },
    });
  });

  it('renders dashboard with sidebar navigation and metrics summary', async () => {
    render(<Dashboard user={mockUser} onLogout={() => {}} />);
    expect(screen.getByText('CareWatch ICU')).toBeInTheDocument();
    expect(screen.getByText('Dr. Sarah Smith')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Admitted Patients')).toBeInTheDocument();
      expect(screen.getByText('Beds Available')).toBeInTheDocument();
      expect(screen.getByText('Active Alerts')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });

  it('switches tabs to Bed Management and Alerts view', async () => {
    render(<Dashboard user={mockUser} onLogout={() => {}} />);
    await waitFor(() => expect(screen.getByText('John Doe')).toBeInTheDocument());

    const bedTabBtn = screen.getByRole('button', { name: /Bed Management/i });
    fireEvent.click(bedTabBtn);
    expect(screen.getAllByText('Bed Management').length).toBeGreaterThan(1);

    const alertTabBtn = screen.getByRole('button', { name: /Alerts/i });
    fireEvent.click(alertTabBtn);
    expect(screen.getAllByText('Clinical Alerts').length).toBeGreaterThan(0);
  });

  it('renders loading indicator while data is being fetched', () => {
    render(<Dashboard user={mockUser} onLogout={() => {}} />);
    expect(screen.getByText(/Loading ICU data/i)).toBeInTheDocument();
  });
});
