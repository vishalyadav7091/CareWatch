import React from 'react';
import { Heart, Activity, Wind, Thermometer, CheckCircle, Radio, StopCircle } from 'lucide-react';

export default function PatientCard({ patient, isStreaming, liveVital, onSelect, onToggleStream }) {
  const v = liveVital || {};
  const bedNum = patient.active_bed?.bed_number || 'UNASSIGNED';

  return (
    <div
      onClick={() => onSelect(patient.id)}
      className={`bg-slate-900 border ${isStreaming ? 'border-sky-500/50' : 'border-slate-800'} hover:border-sky-500/50 transition-all rounded-xl p-5 cursor-pointer shadow-lg`}
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
            {bedNum}
          </span>
          <h3 className="text-lg font-semibold text-white mt-1">
            {patient.first_name} {patient.last_name}
          </h3>
          <p className="text-xs text-slate-400 font-mono">{patient.patient_code}</p>
        </div>
        <span className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${
          isStreaming
            ? 'bg-sky-500/15 text-sky-300 border-sky-500/30'
            : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
        }`}>
          <span className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-sky-400 animate-ping' : 'bg-emerald-500'}`} />
          {isStreaming ? 'Streaming' : 'Monitoring'}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        {[
          { label: 'Heart Rate', val: v.heart_rate ?? 78, unit: 'bpm', icon: Heart, color: 'text-rose-400' },
          { label: 'SpO2', val: v.spo2 ?? 98, unit: '%', icon: Activity, color: 'text-sky-400' },
          { label: 'Resp Rate', val: v.respiratory_rate ?? 16, unit: '/min', icon: Wind, color: 'text-amber-400' },
          { label: 'Temp', val: v.temperature ?? 37.1, unit: '°C', icon: Thermometer, color: 'text-indigo-400' },
        ].map((s) => (
          <div key={s.label} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
            <div className={`flex items-center gap-1.5 text-xs ${s.color} mb-1`}>
              <s.icon className="w-3.5 h-3.5" />
              <span>{s.label}</span>
            </div>
            <div className="text-xl font-bold font-mono text-white">
              {typeof s.val === 'number' ? s.val.toFixed(1) : s.val}{' '}
              <span className="text-xs font-normal text-slate-400">{s.unit}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 text-xs text-slate-400">
        <span className="flex items-center gap-1">
          <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
          {isStreaming ? 'Live Telemetry Active' : 'Vitals Stable'}
        </span>
        <button
          onClick={(e) => { e.stopPropagation(); onToggleStream(patient.id); }}
          className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs transition-colors ${
            isStreaming
              ? 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-400'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
          }`}
        >
          {isStreaming ? <><StopCircle className="w-3 h-3" /> Stop</> : <><Radio className="w-3 h-3" /> Stream</>}
        </button>
      </div>
    </div>
  );
}
