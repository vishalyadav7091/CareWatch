import React from 'react';
import { Bed, Users, CheckCircle, Wrench, UserX } from 'lucide-react';

export default function BedManagement({ beds, onUpdateStatus }) {
  const stats = {
    total: beds.length,
    occupied: beds.filter(b => b.status === 'occupied').length,
    available: beds.filter(b => b.status === 'available').length,
    maintenance: beds.filter(b => b.status === 'maintenance').length,
  };

  const statusStyles = {
    occupied: { bg: 'bg-sky-500/10', border: 'border-sky-500/40', text: 'text-sky-300', badge: 'bg-sky-500/20 text-sky-400' },
    available: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/40', text: 'text-emerald-300', badge: 'bg-emerald-500/20 text-emerald-400' },
    maintenance: { bg: 'bg-amber-500/10', border: 'border-amber-500/40', text: 'text-amber-300', badge: 'bg-amber-500/20 text-amber-400' },
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-white">ICU Bed Management</h2>
        <p className="text-sm text-slate-400">Main ICU – Ward A</p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total Beds', value: stats.total, icon: Bed, color: 'text-slate-300' },
          { label: 'Occupied', value: stats.occupied, icon: Users, color: 'text-sky-400' },
          { label: 'Available', value: stats.available, icon: CheckCircle, color: 'text-emerald-400' },
          { label: 'Maintenance', value: stats.maintenance, icon: Wrench, color: 'text-amber-400' },
        ].map((s) => (
          <div key={s.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className={`text-xs flex items-center gap-1.5 mb-2 ${s.color}`}>
              <s.icon className="w-4 h-4" />
              {s.label}
            </div>
            <div className="text-3xl font-bold font-mono text-white">{s.value}</div>
          </div>
        ))}
      </div>

      {/* Bed Grid */}
      <div className="grid grid-cols-2 gap-4">
        {beds.map((bed) => {
          const st = statusStyles[bed.status] || statusStyles.available;
          return (
            <div key={bed.id} className={`${st.bg} border ${st.border} rounded-xl p-5 transition-all`}>
              <div className="flex justify-between items-start mb-3">
                <div>
                  <span className="text-2xl font-bold font-mono text-white">{bed.bed_number}</span>
                  <p className="text-xs text-slate-400 mt-0.5">{bed.icu_unit_name || 'Main ICU – Ward A'}</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${st.badge} capitalize`}>
                  {bed.status}
                </span>
              </div>

              {bed.current_patient ? (
                <div className="mb-4 p-3 bg-slate-950/40 rounded-lg border border-slate-800/80 text-sm">
                  <p className="text-slate-300 font-semibold">{bed.current_patient.full_name}</p>
                  <p className="text-xs font-mono text-slate-500 mt-0.5">{bed.current_patient.patient_code}</p>
                </div>
              ) : (
                <div className="mb-4 p-3 bg-slate-950/40 rounded-lg border border-dashed border-slate-700 text-sm text-center text-slate-500">
                  <UserX className="w-5 h-5 mx-auto mb-1 opacity-40" />
                  No patient assigned
                </div>
              )}

              <div className="flex gap-2">
                {['available', 'occupied', 'maintenance']
                  .filter((s) => s !== bed.status)
                  .map((s) => (
                    <button
                      key={s}
                      onClick={() => onUpdateStatus(bed.id, s)}
                      className="flex-1 text-xs px-2 py-1.5 bg-slate-800/80 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors capitalize"
                    >
                      → {s}
                    </button>
                  ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

