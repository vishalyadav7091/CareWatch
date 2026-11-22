import React from 'react';
import { Heart, Activity, Wind, Thermometer, Droplets, Radio, Square } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import RiskDashboard from './RiskDashboard';

export default function PatientDetail({ patient, vitals, isStreaming, onToggleStream, onBack }) {
  if (!patient) return null;

  const chartData = [...(vitals || [])]
    .reverse()
    .slice(-20)
    .map((v, i) => ({
      time: `T-${i + 1}`,
      heart_rate: v.heart_rate,
      spo2: v.spo2,
      systolic_bp: v.systolic_bp,
      respiratory_rate: v.respiratory_rate,
      temperature: v.temperature,
    }));

  const latestVital = vitals?.[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={onBack}
          className="text-sm px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 transition-colors"
        >
          ← Back
        </button>
        <div>
          <h2 className="text-xl font-bold text-white">
            {patient.first_name} {patient.last_name}
          </h2>
          <p className="text-sm font-mono text-slate-400">{patient.patient_code}</p>
        </div>
        <span className="ml-auto text-sm px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
          <span className="w-2 h-2 bg-emerald-400 rounded-full animate-ping" />
          Admitted – {patient.admission?.bed_number || 'N/A'}
        </span>
        {onToggleStream && (
          <button
            onClick={() => onToggleStream(patient.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border transition-colors ${
              isStreaming
                ? 'bg-rose-500/10 border-rose-500/30 text-rose-400 hover:bg-rose-500/20'
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
            }`}
          >
            {isStreaming ? <Square className="w-3 h-3" /> : <Radio className="w-3 h-3" />}
            {isStreaming ? 'Stop Stream' : 'Start Stream'}
          </button>
        )}
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { label: 'Heart Rate', value: latestVital?.heart_rate ?? '--', unit: 'bpm',   icon: Heart,       color: 'text-rose-400',   bg: 'bg-rose-500/10' },
          { label: 'SpO2',       value: latestVital?.spo2 ?? '--',       unit: '%',     icon: Activity,    color: 'text-sky-400',    bg: 'bg-sky-500/10' },
          { label: 'BP',         value: latestVital ? `${latestVital.systolic_bp}/${latestVital.diastolic_bp}` : '--', unit: 'mmHg', icon: Droplets, color: 'text-violet-400', bg: 'bg-violet-500/10' },
          { label: 'Resp. Rate', value: latestVital?.respiratory_rate ?? '--', unit: '/min', icon: Wind,   color: 'text-amber-400',  bg: 'bg-amber-500/10' },
          { label: 'Temperature',value: latestVital?.temperature ?? '--', unit: '°C',   icon: Thermometer, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
        ].map((s) => (
          <div key={s.label} className={`${s.bg} border border-slate-800 rounded-xl p-4`}>
            <div className={`flex items-center gap-1.5 text-xs ${s.color} mb-2`}>
              <s.icon className="w-4 h-4" />
              {s.label}
            </div>
            <div className="text-2xl font-bold font-mono text-white">{s.value}</div>
            <div className="text-xs text-slate-500 mt-0.5">{s.unit}</div>
          </div>
        ))}
      </div>

      {/* AI Risk Dashboard */}
      <RiskDashboard patientId={patient.id} />

      {/* Historical Charts */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-4 uppercase tracking-wider">Historical Vitals Trend (Last 20 Readings)</h3>
        {chartData.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-10">No historical data yet. Start a live stream to generate readings.</p>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 11 }} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: 8 }} labelStyle={{ color: '#94a3b8' }} itemStyle={{ color: '#e2e8f0' }} />
              <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
              <Line type="monotone" dataKey="heart_rate"        stroke="#f43f5e" strokeWidth={2} dot={false} name="Heart Rate (bpm)" />
              <Line type="monotone" dataKey="spo2"              stroke="#0ea5e9" strokeWidth={2} dot={false} name="SpO2 (%)" />
              <Line type="monotone" dataKey="respiratory_rate"  stroke="#f59e0b" strokeWidth={2} dot={false} name="Resp. Rate (/min)" />
              <Line type="monotone" dataKey="temperature"       stroke="#8b5cf6" strokeWidth={2} dot={false} name="Temp (°C)" />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Vitals Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-4 uppercase tracking-wider">Recent Readings Log</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-400 border-b border-slate-800">
              <tr>
                {['Time', 'HR (bpm)', 'SpO2 (%)', 'BP (mmHg)', 'RR (/min)', 'Temp (°C)', 'Quality'].map((h) => (
                  <th key={h} className="pb-2 pr-4 font-semibold">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {(vitals || []).slice(0, 10).map((v) => (
                <tr key={v.id} className="text-slate-300">
                  <td className="py-2 pr-4 font-mono text-xs text-slate-400">
                    {v.measured_at ? new Date(v.measured_at).toLocaleTimeString() : '--'}
                  </td>
                  <td className="pr-4 font-mono font-bold text-rose-400">{v.heart_rate}</td>
                  <td className="pr-4 font-mono font-bold text-sky-400">{v.spo2}</td>
                  <td className="pr-4 font-mono text-violet-400">{v.systolic_bp}/{v.diastolic_bp}</td>
                  <td className="pr-4 font-mono text-amber-400">{v.respiratory_rate}</td>
                  <td className="pr-4 font-mono text-indigo-400">{v.temperature}</td>
                  <td>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${v.data_quality === 'valid' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                      {v.data_quality}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {(!vitals || vitals.length === 0) && (
            <p className="text-center text-slate-500 text-sm py-6">No vitals data available.</p>
          )}
        </div>
      </div>
    </div>
  );
}
