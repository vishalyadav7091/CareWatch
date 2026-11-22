import React, { useState } from 'react';
import { AlertTriangle, CheckCircle, Bell, BellOff, ChevronDown, ChevronUp, Clock, ArrowUp } from 'lucide-react';

export default function AlertPanel({ alerts, onAcknowledge, onResolve, onSnooze, onEscalate }) {
  const [statusFilter, setStatusFilter] = useState('active');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [expandedId, setExpandedId] = useState(null);
  const [snoozeInput, setSnoozeInput] = useState({});

  const severityStyle = {
    HIGH:     { bg: 'bg-rose-500/10',   border: 'border-rose-500/30',   text: 'text-rose-400',   badge: 'bg-rose-500/20 text-rose-300' },
    CRITICAL: { bg: 'bg-rose-700/20',   border: 'border-rose-600/50',   text: 'text-rose-300',   badge: 'bg-rose-700/30 text-rose-200' },
    MEDIUM:   { bg: 'bg-amber-500/10',  border: 'border-amber-500/30',  text: 'text-amber-400',  badge: 'bg-amber-500/20 text-amber-300' },
    LOW:      { bg: 'bg-sky-500/10',    border: 'border-sky-500/30',    text: 'text-sky-400',    badge: 'bg-sky-500/20 text-sky-300' },
  };

  const filtered = alerts.filter(a => {
    const matchStatus = statusFilter === 'all' || a.status === statusFilter;
    const matchSev = severityFilter === 'all' || a.severity === severityFilter;
    return matchStatus && matchSev;
  });

  const activeCount = alerts.filter(a => a.status === 'active').length;

  return (
    <div className="space-y-4">
      {/* Header + counts */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Bell className="w-5 h-5 text-rose-400" />
            Clinical Alerts
          </h2>
          <p className="text-sm text-slate-400">
            {activeCount} active · {alerts.length} total
          </p>
        </div>
        <span className="text-xs px-3 py-1 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-full">
          {activeCount} Active
        </span>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {/* Status filter */}
        <div className="flex gap-1 p-1 bg-slate-800/60 rounded-lg">
          {['active', 'acknowledged', 'resolved', 'all'].map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1 text-xs rounded-md capitalize transition-colors ${
                statusFilter === s
                  ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
        {/* Severity filter */}
        <div className="flex gap-1 p-1 bg-slate-800/60 rounded-lg">
          {['all', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(s => (
            <button
              key={s}
              onClick={() => setSeverityFilter(s)}
              className={`px-3 py-1 text-xs rounded-md transition-colors ${
                severityFilter === s
                  ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-10 text-center">
          <BellOff className="w-8 h-8 mx-auto mb-3 text-slate-600" />
          <p className="text-slate-400 text-sm">No alerts match the selected filters.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((alert) => {
            const st = severityStyle[alert.severity] || severityStyle.MEDIUM;
            const expanded = expandedId === alert.id;
            return (
              <div key={alert.id} className={`${st.bg} border ${st.border} rounded-xl`}>
                {/* Summary row */}
                <div
                  className="flex justify-between items-start p-4 cursor-pointer"
                  onClick={() => setExpandedId(expanded ? null : alert.id)}
                >
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <AlertTriangle className={`w-4 h-4 ${st.text} shrink-0`} />
                    <span className="text-sm font-semibold text-white truncate">{alert.alert_type}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${st.badge} shrink-0`}>{alert.severity}</span>
                  </div>
                  <div className="flex items-center gap-2 ml-2 shrink-0">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      alert.status === 'active'
                        ? 'bg-rose-500/20 text-rose-400'
                        : alert.status === 'acknowledged'
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'bg-slate-700 text-slate-400'
                    }`}>
                      {alert.status}
                    </span>
                    {expanded ? <ChevronUp className="w-3.5 h-3.5 text-slate-500" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-500" />}
                  </div>
                </div>

                {/* Expanded detail */}
                {expanded && (
                  <div className="px-4 pb-4 space-y-3 border-t border-slate-800/60 pt-3">
                    <p className="text-sm text-slate-300">{alert.description}</p>
                    <div className="text-xs text-slate-500 space-y-1">
                      <p>Patient: {alert.patient_name || `ID ${alert.patient_id}`} ({alert.patient_code || '—'})</p>
                      <p>Created: {alert.created_at ? new Date(alert.created_at).toLocaleString() : '—'}</p>
                      {alert.snoozed_until && (
                        <p className="text-amber-400">
                          Snoozed until: {new Date(alert.snoozed_until).toLocaleString()}
                        </p>
                      )}
                      {alert.escalated_to_user_id && (
                        <p className="text-violet-400">Escalated to user ID: {alert.escalated_to_user_id}</p>
                      )}
                      {alert.staff_notes && (
                        <p>Notes: {alert.staff_notes}</p>
                      )}
                    </div>

                    {/* Action buttons */}
                    {alert.status !== 'resolved' && (
                      <div className="flex flex-wrap gap-2 pt-1">
                        {alert.status === 'active' && onAcknowledge && (
                          <button
                            onClick={() => onAcknowledge(alert.id)}
                            className="flex items-center gap-1 px-3 py-1.5 bg-slate-800 hover:bg-emerald-500/20 hover:text-emerald-400 text-slate-300 rounded-lg transition-colors text-xs"
                          >
                            <CheckCircle className="w-3.5 h-3.5" /> Acknowledge
                          </button>
                        )}
                        {onResolve && (
                          <button
                            onClick={() => onResolve(alert.id)}
                            className="flex items-center gap-1 px-3 py-1.5 bg-slate-800 hover:bg-sky-500/20 hover:text-sky-400 text-slate-300 rounded-lg transition-colors text-xs"
                          >
                            Resolve
                          </button>
                        )}
                        {onSnooze && (
                          <div className="flex items-center gap-1">
                            <input
                              type="number"
                              min="1"
                              max="120"
                              placeholder="min"
                              value={snoozeInput[alert.id] || ''}
                              onChange={e => setSnoozeInput(p => ({ ...p, [alert.id]: e.target.value }))}
                              className="w-14 text-xs bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-300"
                            />
                            <button
                              onClick={() => { onSnooze(alert.id, parseInt(snoozeInput[alert.id] || 15)); setSnoozeInput(p => ({ ...p, [alert.id]: '' })); }}
                              className="flex items-center gap-1 px-3 py-1.5 bg-slate-800 hover:bg-amber-500/20 hover:text-amber-400 text-slate-300 rounded-lg transition-colors text-xs"
                            >
                              <Clock className="w-3.5 h-3.5" /> Snooze
                            </button>
                          </div>
                        )}
                        {onEscalate && (
                          <button
                            onClick={() => onEscalate(alert.id)}
                            className="flex items-center gap-1 px-3 py-1.5 bg-slate-800 hover:bg-violet-500/20 hover:text-violet-400 text-slate-300 rounded-lg transition-colors text-xs"
                          >
                            <ArrowUp className="w-3.5 h-3.5" /> Escalate
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
