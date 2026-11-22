import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import AlertPanel from '../components/AlertPanel';

const mockAlerts = [
  {
    id: 101,
    patient_id: 1,
    patient_name: 'John Doe',
    patient_code: 'PAT-2026-001',
    alert_type: 'Tachycardia',
    severity: 'CRITICAL',
    description: 'Heart rate 155 bpm exceeds threshold',
    status: 'active',
    created_at: new Date().toISOString(),
  },
  {
    id: 102,
    patient_id: 1,
    patient_name: 'John Doe',
    patient_code: 'PAT-2026-001',
    alert_type: 'Hypoxia',
    severity: 'WARNING',
    description: 'SpO2 91% below threshold',
    status: 'acknowledged',
    created_at: new Date().toISOString(),
  },
];

describe('AlertPanel Component', () => {
  it('displays active alert count', () => {
    render(<AlertPanel alerts={mockAlerts} />);
    const activeBadges = screen.getAllByText(/1 Active/i);
    expect(activeBadges.length).toBeGreaterThan(0);
  });

  it('renders alert cards with severity tags', () => {
    render(<AlertPanel alerts={mockAlerts} />);
    expect(screen.getByText('Tachycardia')).toBeInTheDocument();
    const criticalTags = screen.getAllByText('CRITICAL');
    expect(criticalTags.length).toBeGreaterThan(0);
  });

  it('filters alerts when clicking filter button', () => {
    render(<AlertPanel alerts={mockAlerts} />);
    const ackFilterBtn = screen.getByRole('button', { name: /^acknowledged$/i });
    fireEvent.click(ackFilterBtn);
    expect(screen.getByText('Hypoxia')).toBeInTheDocument();
    expect(screen.queryByText('Tachycardia')).not.toBeInTheDocument();
  });

  it('expands alert detail and triggers acknowledge workflow', () => {
    const onAcknowledge = vi.fn();
    render(<AlertPanel alerts={mockAlerts} onAcknowledge={onAcknowledge} />);
    const cardHeader = screen.getByText('Tachycardia').closest('.cursor-pointer');
    fireEvent.click(cardHeader);
    expect(screen.getByText(/Heart rate 155 bpm exceeds threshold/i)).toBeInTheDocument();
    const ackBtn = screen.getByRole('button', { name: /^Acknowledge$/i });
    fireEvent.click(ackBtn);
    expect(onAcknowledge).toHaveBeenCalledWith(101);
  });
});
