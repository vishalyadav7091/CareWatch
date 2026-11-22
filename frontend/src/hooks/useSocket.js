import { useEffect, useRef, useState, useCallback } from 'react';
import { io } from 'socket.io-client';

const SOCKET_URL = 'http://127.0.0.1:5000';

export function useSocket() {
  const socketRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);

  useEffect(() => {
    const socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 2000,
      timeout: 5000,
    });

    socket.on('connect', () => {
      setConnected(true);
      setConnectionError(null);
      console.log('[SocketIO] Connected:', socket.id);
    });

    socket.on('disconnect', (reason) => {
      setConnected(false);
      console.log('[SocketIO] Disconnected:', reason);
    });

    socket.on('connect_error', (err) => {
      setConnectionError(err.message);
      setConnected(false);
      console.warn('[SocketIO] Connection error:', err.message);
    });

    socketRef.current = socket;

    return () => {
      socket.disconnect();
    };
  }, []);

  const joinPatientRoom = useCallback((patientId) => {
    socketRef.current?.emit('join_patient_room', { patient_id: patientId });
  }, []);

  const leavePatientRoom = useCallback((patientId) => {
    socketRef.current?.emit('leave_patient_room', { patient_id: patientId });
  }, []);

  const startLiveStream = useCallback((patientId, scenario = 'stable') => {
    socketRef.current?.emit('start_live_stream', { patient_id: patientId, scenario });
  }, []);

  const stopLiveStream = useCallback((patientId) => {
    socketRef.current?.emit('stop_live_stream', { patient_id: patientId });
  }, []);

  const onVitalUpdate = useCallback((handler) => {
    const sock = socketRef.current;
    sock?.on('vital_update', handler);
    return () => sock?.off('vital_update', handler);
  }, []);

  const ping = useCallback(() => {
    socketRef.current?.emit('ping_server', { ts: Date.now() });
  }, []);

  return {
    getSocket: () => socketRef.current,
    connected,
    connectionError,
    joinPatientRoom,
    leavePatientRoom,
    startLiveStream,
    stopLiveStream,
    onVitalUpdate,
    ping,
  };
}

