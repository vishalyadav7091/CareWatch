import React, { useEffect, useState } from 'react';
import { Wifi, WifiOff, Radio } from 'lucide-react';

export default function ConnectionStatus({ connected, error, livePatients = 0 }) {
  const [blink, setBlink] = useState(true);

  useEffect(() => {
    const t = setInterval(() => setBlink(b => !b), 1000);
    return () => clearInterval(t);
  }, []);

  if (connected) {
    return (
      <div className="flex items-center gap-2 text-xs text-emerald-400">
        <span className={`w-2 h-2 rounded-full bg-emerald-400 ${blink ? 'opacity-100' : 'opacity-30'} transition-opacity`} />
        <Wifi className="w-3.5 h-3.5" />
        <span>Live</span>
        {livePatients > 0 && (
          <span className="flex items-center gap-1 ml-1 text-sky-400">
            <Radio className="w-3 h-3" />
            {livePatients} streaming
          </span>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-xs text-rose-400">
      <WifiOff className="w-3.5 h-3.5" />
      <span>{error ? 'Backend offline' : 'Connecting...'}</span>
    </div>
  );
}

