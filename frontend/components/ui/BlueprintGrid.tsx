'use client'

import React from 'react'

export default function BlueprintGrid() {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-[0.03] select-none">
      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="smallGrid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="white" strokeWidth="0.5"/>
          </pattern>
          <pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse">
            <rect width="100" height="100" fill="url(#smallGrid)"/>
            <path d="M 100 0 L 0 0 0 100" fill="none" stroke="white" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
        
        {/* Subtle coordinate labels */}
        {Array.from({ length: 10 }).map((_, i) => (
          <React.Fragment key={i}>
            <text x="5" y={(i + 1) * 100 - 5} fill="white" fontSize="8" fontFamily="monospace">
              {(i + 1) * 100}
            </text>
            <text x={(i + 1) * 100 + 5} y="15" fill="white" fontSize="8" fontFamily="monospace">
              {String.fromCharCode(65 + i)}
            </text>
          </React.Fragment>
        ))}
      </svg>
    </div>
  )
}
