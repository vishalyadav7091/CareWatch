import React, { useState, useEffect } from 'react';
import { Users, Stethoscope, HeartPulse, Search, ShieldCheck, Mail, Building, CheckCircle2 } from 'lucide-react';
import { clinicalService } from '../services/api';

export default function StaffManagement() {
  const [doctors, setDoctors] = useState([]);
  const [nurses, setNurses] = useState([]);
  const [summary, setSummary] = useState({ total_staff: 0, doctors_count: 0, nurses_count: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // 'all', 'doctor', 'nurse'
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchStaff();
  }, []);

  const fetchStaff = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await clinicalService.getStaffDirectory();
      if (res.data && res.data.success) {
        setDoctors(res.data.doctors || []);
        setNurses(res.data.nurses || []);
        setSummary(res.data.summary || {});
      }
    } catch (err) {
      setError('Failed to load staff roster. Please check admin permissions.');
    } finally {
      setLoading(false);
    }
  };

  const allStaff = [
    ...doctors.map(d => ({ ...d, staffType: 'doctor' })),
    ...nurses.map(n => ({ ...n, staffType: 'nurse' })),
  ];

  const filteredStaff = allStaff.filter(item => {
    const matchType = filter === 'all' || item.staffType === filter;
    const q = search.toLowerCase();
    const matchSearch =
      !search ||
      (item.name && item.name.toLowerCase().includes(q)) ||
      (item.email && item.email.toLowerCase().includes(q)) ||
      (item.specialization && item.specialization.toLowerCase().includes(q)) ||
      (item.department && item.department.toLowerCase().includes(q));
    return matchType && matchSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-purple-400" />
            Medical Staff Roster & Directory
          </h2>
          <p className="text-sm text-slate-400">
            Administrative record of all registered Doctors and ICU Nurses
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-3 py-1 bg-purple-500/10 border border-purple-500/20 text-purple-300 rounded-full font-medium">
            Admin Console Access
          </span>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-4">
          <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-white">{summary.total_staff || allStaff.length}</div>
            <div className="text-xs text-slate-400">Total Registered Staff</div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-4">
          <div className="p-3 bg-sky-500/10 rounded-xl text-sky-400">
            <Stethoscope className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-white">{doctors.length}</div>
            <div className="text-xs text-sky-400 font-medium">Doctors / Specialists</div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-4">
          <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400">
            <HeartPulse className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-white">{nurses.length}</div>
            <div className="text-xs text-emerald-400 font-medium">ICU Staff Nurses</div>
          </div>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row justify-between gap-3">
        <div className="flex gap-1.5 p-1 bg-slate-900 border border-slate-800 rounded-lg">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              filter === 'all' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            All Staff ({allStaff.length})
          </button>
          <button
            onClick={() => setFilter('doctor')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              filter === 'doctor' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Doctors ({doctors.length})
          </button>
          <button
            onClick={() => setFilter('nurse')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              filter === 'nurse' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Nurses ({nurses.length})
          </button>
        </div>

        <div className="relative min-w-[260px]">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search by name, dept, or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500"
          />
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-center py-12 text-slate-400">Loading staff directory...</div>
      ) : error ? (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl text-sm">
          {error}
        </div>
      ) : filteredStaff.length === 0 ? (
        <div className="text-center py-12 text-slate-500 bg-slate-900/50 border border-slate-800/60 rounded-xl">
          No medical staff records found.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredStaff.map((staff) => {
            const isDoc = staff.staffType === 'doctor';
            return (
              <div
                key={`${staff.staffType}-${staff.id}`}
                className={`bg-slate-900 border rounded-xl p-5 transition-all hover:border-slate-700 ${
                  isDoc ? 'border-sky-500/20' : 'border-emerald-500/20'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${
                        isDoc
                          ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
                          : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                      }`}
                    >
                      {isDoc ? 'Dr' : 'RN'}
                    </div>
                    <div>
                      <h3 className="font-semibold text-white text-sm leading-snug">{staff.name}</h3>
                      <span
                        className={`inline-block text-[10px] font-medium px-2 py-0.5 rounded-full mt-0.5 ${
                          isDoc
                            ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        }`}
                      >
                        {isDoc ? 'Physician / Specialist' : 'Staff Nurse'}
                      </span>
                    </div>
                  </div>
                  <span className="flex items-center gap-1 text-[11px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    <CheckCircle2 className="w-3 h-3" />
                    Active
                  </span>
                </div>

                <div className="space-y-2 text-xs pt-3 border-t border-slate-800/80">
                  <div className="flex items-center gap-2 text-slate-300">
                    <Building className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                    <span className="truncate">
                      {isDoc ? staff.specialization : staff.department || 'ICU Critical Care'}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-slate-400">
                    <Mail className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                    <span className="truncate">{staff.email}</span>
                  </div>

                  <div className="flex justify-between items-center pt-2 text-[11px] text-slate-500">
                    <span>Hospital: {staff.hospital || 'City General'}</span>
                    <span>ID: #{staff.id}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
