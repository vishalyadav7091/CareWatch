import React, { useState } from 'react';
import { Activity, Lock, Mail, AlertCircle, Stethoscope, HeartPulse, ShieldCheck } from 'lucide-react';
import { authService } from '../services/api';

const DEMO_USERS = [
  {
    role: 'Doctor',
    icon: Stethoscope,
    email: 'doctor.smith@carewatch.local',
    name: 'Dr. Sarah Smith',
    color: 'border-sky-500/40 text-sky-400 bg-sky-500/10 hover:bg-sky-500/20',
    activeColor: 'border-sky-500 bg-sky-500/25 text-sky-300 ring-2 ring-sky-500/40',
  },
  {
    role: 'Nurse',
    icon: HeartPulse,
    email: 'nurse.jack@carewatch.local',
    name: 'Nurse Jack Robinson',
    color: 'border-emerald-500/40 text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20',
    activeColor: 'border-emerald-500 bg-emerald-500/25 text-emerald-300 ring-2 ring-emerald-500/40',
  },
  {
    role: 'Admin',
    icon: ShieldCheck,
    email: 'admin@carewatch.local',
    name: 'System Administrator',
    color: 'border-purple-500/40 text-purple-400 bg-purple-500/10 hover:bg-purple-500/20',
    activeColor: 'border-purple-500 bg-purple-500/25 text-purple-300 ring-2 ring-purple-500/40',
  },
];

export default function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState('doctor.smith@carewatch.local');
  const [password, setPassword] = useState('Password#123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const selectDemoUser = (userEmail) => {
    setEmail(userEmail);
    setPassword('Password#123');
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await authService.login(email, password);
      onLoginSuccess(data.user);
    } catch (err) {
      if (!err.response || err.response.status === 502 || err.response.status === 504) {
        setError('Cannot reach CareWatch backend (502 Bad Gateway). Make sure Flask server is running on port 5000.');
      } else if (err.response.status === 401) {
        setError(err.response?.data?.error || 'Authentication failed. Please verify credentials.');
      } else {
        setError(err.response?.data?.error || `Server error (${err.response.status}). Please check Flask backend.`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-2xl">
        <div className="flex flex-col items-center mb-6">
          <div className="p-3 bg-sky-500/10 rounded-full mb-3 text-sky-400">
            <Activity className="w-10 h-10 animate-pulse" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide">CareWatch ICU</h1>
          <p className="text-sm text-slate-400">AI-Powered Patient Monitoring System</p>
        </div>

        {/* Quick 1-Click Role Switcher */}
        <div className="mb-5">
          <label className="block text-xs font-semibold uppercase text-slate-400 mb-2">
            Select Role (Quick Login)
          </label>
          <div className="grid grid-cols-3 gap-2">
            {DEMO_USERS.map((u) => {
              const Icon = u.icon;
              const isSelected = email === u.email;
              return (
                <button
                  key={u.role}
                  type="button"
                  onClick={() => selectDemoUser(u.email)}
                  className={`p-2.5 rounded-lg border text-xs font-medium flex flex-col items-center gap-1.5 transition-all ${
                    isSelected ? u.activeColor : u.color
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{u.role}</span>
                </button>
              );
            })}
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-center gap-2 text-rose-400 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase text-slate-400 mb-1">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 w-5 h-5 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-sky-500 text-sm"
                placeholder="doctor@carewatch.local"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-400 mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 w-5 h-5 text-slate-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-sky-500 text-sm"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-medium rounded-lg transition-colors text-sm shadow-lg shadow-sky-600/20"
          >
            {loading ? 'Authenticating...' : 'Sign In to ICU Central'}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-slate-800 text-center text-xs text-slate-500 space-y-1">
          <p>Demo Account: doctor.smith@carewatch.local / Password#123</p>
          <p className="text-slate-600">Available: doctor, nurse, admin (Password#123)</p>
        </div>
      </div>
    </div>
  );
}

