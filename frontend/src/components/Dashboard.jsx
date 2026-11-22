import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity, Users, BedDouble, Bell, LogOut, RefreshCw, AlertTriangle, Radio
} from 'lucide-react';
import { clinicalService } from '../services/api';
import { useSocket } from '../hooks/useSocket';
import PatientCard from './PatientCard';
import PatientDetail from './PatientDetail';
import BedManagement from './BedManagement';
import AlertPanel from './AlertPanel';
import ConnectionStatus from './ConnectionStatus';

const NAV = [
  { id: 'dashboard', label: 'ICU Dashboard', icon: Activity },
  { id: 'beds', label: 'Bed Management', icon: BedDouble },
  { id: 'alerts', label: 'Alerts', icon: Bell },
];

export default function Dashboard({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [patients, setPatients] = useState([]);
  const [beds, setBeds] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [vitals, setVitals] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState(null);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);
  const [streamingPatients, setStreamingPatients] = useState(new Set());
  const [liveVitals, setLiveVitals] = useState({});

  const {
    connected, connectionError,
    joinPatientRoom, leavePatientRoom,
    startLiveStream, stopLiveStream,
    onVitalUpdate,
  } = useSocket();

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  // Live vital update handler
  useEffect(() => {
    const cleanup = onVitalUpdate((payload) => {
      const { patient_id, data } = payload;
      setLiveVitals(prev => ({ ...prev, [patient_id]: data }));

      // If this patient is currently viewed, prepend to vitals list
      if (selectedPatientId === patient_id) {
        setVitals(prev => [data, ...prev].slice(0, 50));
      }
    });
    return cleanup;
  }, [onVitalUpdate, selectedPatientId]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [pRes, bRes, aRes] = await Promise.all([
        clinicalService.getPatients(),
        clinicalService.getBeds(),
        clinicalService.getAlerts('all'),
      ]);
      setPatients(pRes.data.data || []);
      setBeds(bRes.data.data || []);
      setAlerts(aRes.data.data || []);
    } catch {
      setError('Could not connect to CareWatch backend. Please ensure the Flask server is running.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSelectPatient = async (patientId) => {
    try {
      const [detailRes, vitalsRes] = await Promise.all([
        clinicalService.getPatientDetails(patientId),
        clinicalService.getPatientVitals(patientId, 20),
      ]);
      setSelectedPatient(detailRes.data.data);
      setVitals(vitalsRes.data.data || []);
      setSelectedPatientId(patientId);
      joinPatientRoom(patientId);
      setActiveTab('dashboard');
    } catch {
      showToast('Failed to load patient details.');
    }
  };

  const handleBackFromPatient = () => {
    if (selectedPatientId) leavePatientRoom(selectedPatientId);
    setSelectedPatientId(null);
    setSelectedPatient(null);
    setVitals([]);
  };

  const handleToggleStream = (patientId) => {
    const isStreaming = streamingPatients.has(patientId);
    const scenarios = ['stable', 'arrhythmia_tachycardia', 'desaturation_hypoxia'];
    const sc = scenarios[Math.floor(Math.random() * scenarios.length)];

    if (isStreaming) {
      stopLiveStream(patientId);
      setStreamingPatients(prev => { const s = new Set(prev); s.delete(patientId); return s; });
      showToast(`Live stream stopped for patient ${patientId}`);
    } else {
      joinPatientRoom(patientId);
      startLiveStream(patientId, sc);
      setStreamingPatients(prev => new Set([...prev, patientId]));
      showToast(`Live stream started: ${sc}`);
    }
  };

  const handleUpdateBedStatus = async (bedId, status) => {
    try {
      await clinicalService.updateBedStatus(bedId, status);
      showToast(`Bed status updated to ${status}`);
      await loadData();
    } catch {
      showToast('Failed to update bed status.');
    }
  };

  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await clinicalService.acknowledgeAlert(alertId);
      showToast('Alert acknowledged.');
      const aRes = await clinicalService.getAlerts('all');
      setAlerts(aRes.data.data || []);
    } catch {
      showToast('Failed to acknowledge alert.');
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await clinicalService.resolveAlert(alertId);
      showToast('Alert resolved.');
      const aRes = await clinicalService.getAlerts('all');
      setAlerts(aRes.data.data || []);
    } catch {
      showToast('Failed to resolve alert.');
    }
  };

  const handleSnoozeAlert = async (alertId, durationMinutes) => {
    try {
      await clinicalService.snoozeAlert(alertId, durationMinutes);
      showToast(`Alert snoozed for ${durationMinutes} min.`);
      const aRes = await clinicalService.getAlerts('all');
      setAlerts(aRes.data.data || []);
    } catch {
      showToast('Failed to snooze alert.');
    }
  };

  const handleEscalateAlert = async (alertId) => {
    try {
      await clinicalService.escalateAlert(alertId, user?.id || 1);
      showToast('Alert escalated.');
      const aRes = await clinicalService.getAlerts('all');
      setAlerts(aRes.data.data || []);
    } catch {
      showToast('Failed to escalate alert.');
    }
  };

  const activeAlertCount = alerts.filter(a => a.status === 'active').length;

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
        <div className="p-5 border-b border-slate-800 flex items-center gap-3">
          <div className="p-2 bg-sky-500/10 rounded-lg text-sky-400">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white leading-tight">CareWatch ICU</h1>
            <p className="text-xs text-slate-400">AI Patient Monitor</p>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {NAV.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => { setActiveTab(id); if (id !== 'dashboard') { setSelectedPatientId(null); setSelectedPatient(null); } }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors relative ${
                activeTab === id
                  ? 'bg-sky-500/15 text-sky-400 border border-sky-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
              {id === 'alerts' && activeAlertCount > 0 && (
                <span className="ml-auto text-xs bg-rose-500 text-white px-1.5 py-0.5 rounded-full">
                  {activeAlertCount}
                </span>
              )}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-800 space-y-3">
          <ConnectionStatus
            connected={connected}
            error={connectionError}
            livePatients={streamingPatients.size}
          />
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-sky-500/20 flex items-center justify-center text-sky-400 font-bold text-sm">
              {user?.full_name?.[0] || 'U'}
            </div>
            <div className="text-sm">
              <p className="text-white font-medium leading-tight truncate max-w-[120px]">{user?.full_name || 'Staff'}</p>
              <p className="text-slate-500 text-xs capitalize">{user?.role}</p>
            </div>
          </div>
          <button
            onClick={onLogout}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
          <div>
            <h2 className="text-base font-semibold text-white">
              {activeTab === 'dashboard' && selectedPatientId ? 'Patient Details' :
               activeTab === 'dashboard' ? 'ICU Dashboard' :
               activeTab === 'beds' ? 'Bed Management' : 'Clinical Alerts'}
            </h2>
            <p className="text-xs text-slate-400">City General Hospital · Main ICU – Ward A</p>
          </div>
          <div className="flex items-center gap-3">
            {connected && (
              <span className="text-xs flex items-center gap-1 text-emerald-400">
                <Radio className="w-3.5 h-3.5" />
                Real-time Active
              </span>
            )}
            <button
              onClick={loadData}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
          </div>
        </header>

        <div className="p-6">
          {error && (
            <div className="mb-4 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-center gap-3 text-rose-400">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {loading && (
            <div className="flex items-center justify-center py-20 text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin mr-2" />
              Loading ICU data...
            </div>
          )}

          {/* Dashboard */}
          {!loading && activeTab === 'dashboard' && !selectedPatientId && (
            <>
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="flex items-center gap-2 text-xs text-sky-400 mb-2"><Users className="w-4 h-4" /> Admitted Patients</div>
                  <div className="text-3xl font-bold font-mono text-white">{patients.length}</div>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="flex items-center gap-2 text-xs text-emerald-400 mb-2"><BedDouble className="w-4 h-4" /> Beds Available</div>
                  <div className="text-3xl font-bold font-mono text-white">{beds.filter(b => b.status === 'available').length}</div>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="flex items-center gap-2 text-xs text-rose-400 mb-2"><Bell className="w-4 h-4" /> Active Alerts</div>
                  <div className="text-3xl font-bold font-mono text-white">{activeAlertCount}</div>
                </div>
              </div>

              {patients.length === 0 ? (
                <div className="text-center py-16 text-slate-500">
                  <Users className="w-10 h-10 mx-auto mb-3 opacity-30" />
                  <p>No patients currently admitted.</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 xl:grid-cols-3 gap-4">
                  {patients.map((p) => (
                    <PatientCard
                      key={p.id}
                      patient={p}
                      isStreaming={streamingPatients.has(p.id)}
                      liveVital={liveVitals[p.id]}
                      onSelect={handleSelectPatient}
                      onToggleStream={handleToggleStream}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          {!loading && activeTab === 'dashboard' && selectedPatientId && selectedPatient && (
            <PatientDetail
              patient={selectedPatient}
              vitals={vitals}
              isStreaming={streamingPatients.has(selectedPatientId)}
              onToggleStream={handleToggleStream}
              onBack={handleBackFromPatient}
            />
          )}

          {!loading && activeTab === 'beds' && (
            <BedManagement beds={beds} onUpdateStatus={handleUpdateBedStatus} />
          )}

          {!loading && activeTab === 'alerts' && (
            <AlertPanel
              alerts={alerts}
              onAcknowledge={handleAcknowledgeAlert}
              onResolve={handleResolveAlert}
              onSnooze={handleSnoozeAlert}
              onEscalate={handleEscalateAlert}
            />
          )}
        </div>
      </main>

      {toastMsg && (
        <div className="fixed bottom-5 right-5 bg-slate-800 border border-slate-700 text-slate-100 px-4 py-2.5 rounded-lg shadow-xl text-sm z-50 transition-all">
          {toastMsg}
        </div>
      )}
    </div>
  );
}
