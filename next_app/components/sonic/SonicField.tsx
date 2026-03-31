'use client'

import { useState, useCallback } from 'react'
import { useSonicEngine, type SonicFieldInput } from './useSonicEngine'

interface SonicFieldProps {
  input: SonicFieldInput
  subjectName: string
  className?: string
}

export function SonicField({ input, subjectName, className = '' }: SonicFieldProps) {
  const [volume, setVolumeState] = useState(-12)
  const engine = useSonicEngine(input)

  const handleToggle = useCallback(async () => {
    if (engine.isPlaying) {
      engine.stop()
    } else {
      await engine.start()
    }
  }, [engine])

  const handleVolume = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const db = Number(e.target.value)
    setVolumeState(db)
    engine.setVolume(db)
  }, [engine])

  return (
    // Root: only the button determines layout height — slider panel is absolutely positioned
    <div className={`relative flex items-center ${className}`}>
      {/* Play / Stop button */}
      <button
        onClick={handleToggle}
        disabled={!engine.isReady}
        aria-label={engine.isPlaying ? 'Detener firma sonora' : 'Reproducir firma sonora'}
        className={[
          'flex items-center justify-center w-9 h-9',
          'rounded-full border border-muted-foreground/30',
          'bg-transparent text-muted-foreground',
          'hover:border-muted-foreground/60 transition-colors',
          'disabled:opacity-40 disabled:cursor-not-allowed',
          engine.isPlaying ? 'sonic-pulse' : '',
        ].join(' ')}
      >
        <span className="text-base leading-none select-none">
          {engine.isPlaying ? '■' : '♪'}
        </span>
      </button>

      {/* Volume slider + label — floats below the button, out of flow */}
      <div
        className="absolute top-full right-0 mt-2 flex flex-col items-end gap-1"
        style={{
          opacity: engine.isPlaying ? 1 : 0,
          transition: 'opacity 300ms ease',
          pointerEvents: engine.isPlaying ? 'auto' : 'none',
        }}
      >
        <input
          type="range"
          min={-30}
          max={0}
          step={1}
          value={volume}
          onChange={handleVolume}
          aria-label="Volumen de la firma sonora"
          className="w-24 h-1 accent-muted-foreground cursor-pointer"
        />
        <p className="text-[11px] text-muted-foreground/60 tracking-wide whitespace-nowrap">
          Firma sonora natal · {subjectName}
        </p>
      </div>

      {/* Pulse keyframe */}
      <style>{`
        @keyframes sonicPulse {
          0%, 100% { opacity: 0.7; }
          50%       { opacity: 1;   }
        }
        .sonic-pulse {
          animation: sonicPulse 3s ease-in-out infinite;
        }
      `}</style>
    </div>
  )
}
