import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import RiskDashboard from '../components/RiskDashboard';
import * as apiModule from '../services/api';

describe('RiskDashboard Component', () => {
  it('renders the mandatory research & clinical disclaimer', async () => {
    vi.spyOn(apiModule.clinicalService, 'getMLStatus').mockResolvedValue({
      data: { model_ready: true, version: '1.0.0-demo' }
    });
    vi.spyOn(apiModule.clinicalService, 'getPatientRisk').mockResolvedValue({
      data: { success: true, experimental_risk_score: 35.5, risk_category: 'LOW', model_version: '1.0.0-demo', vitals_window_size: 10 }
    });
    vi.spyOn(apiModule.clinicalService, 'getRiskHistory').mockResolvedValue({
      data: { data: [] }
    });

    render(<RiskDashboard patientId={1} />);
    expect(screen.getByText(/RESEARCH \/ DEMONSTRATION ONLY/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('LOW')).toBeInTheDocument();
      expect(screen.getByText('35.5')).toBeInTheDocument();
    });
  });

  it('renders model not ready state when model_ready is false', async () => {
    vi.spyOn(apiModule.clinicalService, 'getMLStatus').mockResolvedValue({
      data: { model_ready: false }
    });
    vi.spyOn(apiModule.clinicalService, 'getPatientRisk').mockRejectedValue({
      response: { data: { error: 'No model' } }
    });
    vi.spyOn(apiModule.clinicalService, 'getRiskHistory').mockResolvedValue({ data: { data: [] } });

    render(<RiskDashboard patientId={1} />);
    await waitFor(() => {
      expect(screen.getByText(/Model not trained yet/i)).toBeInTheDocument();
    });
  });
});
