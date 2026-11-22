import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import Login from '../components/Login';

describe('Login Component', () => {
  it('renders login form with email, password fields and sign in button', () => {
    render(<Login onLoginSuccess={() => {}} />);
    expect(screen.getByText('CareWatch ICU')).toBeInTheDocument();
    expect(screen.getByText(/AI-Powered Patient Monitoring System/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('doctor@carewatch.local')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In to ICU Central/i })).toBeInTheDocument();
  });

  it('allows filling in credentials', () => {
    render(<Login onLoginSuccess={() => {}} />);
    const emailInput = screen.getByPlaceholderText('doctor@carewatch.local');
    const pwInput = screen.getByPlaceholderText('••••••••');
    fireEvent.change(emailInput, { target: { value: 'nurse.jack@carewatch.local' } });
    fireEvent.change(pwInput, { target: { value: 'Password#123' } });
    expect(emailInput.value).toBe('nurse.jack@carewatch.local');
    expect(pwInput.value).toBe('Password#123');
  });

  it('renders demo account helper text', () => {
    render(<Login onLoginSuccess={() => {}} />);
    expect(screen.getByText(/Demo Account: doctor.smith@carewatch.local/i)).toBeInTheDocument();
  });
});
