import React from 'react';
import { Check, Circle } from 'lucide-react';
import { ApplicationStage } from '../types';

interface StageStepperProps {
  currentStage: ApplicationStage;
}

const STAGES: { key: ApplicationStage; label: string }[] = [
  { key: 'APPLIED', label: 'Applied' },
  { key: 'SHORTLISTED', label: 'Shortlisted' },
  { key: 'INTERVIEW_SCHEDULED', label: 'Interview Scheduled' },
  { key: 'INTERVIEWED', label: 'Interviewed' },
  { key: 'OFFERED', label: 'Offered' },
  { key: 'ACCEPTED', label: 'Accepted' },
];

export const StageStepper: React.FC<StageStepperProps> = ({ currentStage }) => {
  const currentIndex = STAGES.findIndex((s) => s.key === currentStage);

  return (
    <div className="w-full py-4">
      <div className="flex items-center justify-between relative">
        {/* Connecting Line Background */}
        <div className="absolute left-6 right-6 top-1/2 -translate-y-1/2 h-1 bg-slate-200 z-0" />
        
        {/* Active Progress Bar */}
        <div 
          className="absolute left-6 top-1/2 -translate-y-1/2 h-1 bg-teal-500 z-0 transition-all duration-500"
          style={{ 
            width: currentIndex >= 0 ? `${(currentIndex / (STAGES.length - 1)) * (100 - (12 / 100))}%` : '0%' 
          }}
        />

        {STAGES.map((stage, idx) => {
          const isCompleted = idx < currentIndex;
          const isCurrent = idx === currentIndex;

          return (
            <div key={stage.key} className="flex flex-col items-center relative z-10">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-semibold text-xs transition-all duration-300 ${
                  isCompleted
                    ? 'bg-teal-600 text-white shadow-md shadow-teal-600/30 ring-4 ring-white'
                    : isCurrent
                    ? 'bg-teal-600 text-white ring-4 ring-teal-100 shadow-lg scale-110'
                    : 'bg-white border-2 border-slate-300 text-slate-400'
                }`}
              >
                {isCompleted ? (
                  <Check className="w-4 h-4 stroke-[3]" />
                ) : (
                  <span>{idx + 1}</span>
                )}
              </div>
              <span
                className={`mt-2 text-xs text-center max-w-[80px] font-medium leading-tight ${
                  isCurrent
                    ? 'text-teal-700 font-bold'
                    : isCompleted
                    ? 'text-slate-800'
                    : 'text-slate-400'
                }`}
              >
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
