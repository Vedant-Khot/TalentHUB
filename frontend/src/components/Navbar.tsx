import React from 'react';
import { Calendar, UserCheck, RefreshCw, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface NavbarProps {
  title: string;
  subtitle?: string;
  seasonName?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ title, subtitle, seasonName = "2026-2027 Campus Drive" }) => {
  const { user, switchDemoUser, isLoading } = useAuth();

  return (
    <header className="bg-white border-b border-slate-200 px-8 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 sticky top-0 z-10 shadow-xs">
      <div>
        <h2 className="text-xl font-bold text-slate-800">{title}</h2>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center flex-wrap gap-3">
        {/* Active Placement Season Pill */}
        <div className="flex items-center space-x-2 bg-slate-100 text-slate-700 px-3 py-1.5 rounded-full text-xs font-medium border border-slate-200">
          <Calendar className="w-3.5 h-3.5 text-teal-600" />
          <span>{seasonName}</span>
        </div>

        {/* Demo Role Switcher Pill */}
        <div className="flex items-center bg-teal-50 border border-teal-200 rounded-lg p-1 space-x-1 text-xs">
          <span className="text-[11px] font-semibold text-teal-800 px-2 flex items-center gap-1">
            <UserCheck className="w-3 h-3 text-teal-600" /> Test Roles:
          </span>
          <button
            onClick={() => switchDemoUser('student1')}
            disabled={isLoading}
            className={`px-2 py-1 rounded font-medium transition-all ${
              user?.email === 'student1@college.edu'
                ? 'bg-teal-600 text-white shadow-xs'
                : 'text-slate-600 hover:bg-teal-100/60'
            }`}
          >
            Aarav (CSE 9.15)
          </button>
          <button
            onClick={() => switchDemoUser('student2')}
            disabled={isLoading}
            className={`px-2 py-1 rounded font-medium transition-all ${
              user?.email === 'student2@college.edu'
                ? 'bg-teal-600 text-white shadow-xs'
                : 'text-slate-600 hover:bg-teal-100/60'
            }`}
          >
            Priya (ECE 7.40)
          </button>
          <button
            onClick={() => switchDemoUser('student3')}
            disabled={isLoading}
            className={`px-2 py-1 rounded font-medium transition-all ${
              user?.email === 'student3@college.edu'
                ? 'bg-teal-600 text-white shadow-xs'
                : 'text-slate-600 hover:bg-teal-100/60'
            }`}
          >
            Rohan (MECH 8.20)
          </button>
          <button
            onClick={() => switchDemoUser('coordinator')}
            disabled={isLoading}
            className={`px-2 py-1 rounded font-medium transition-all ${
              user?.role === 'PLACEMENT_COORDINATOR'
                ? 'bg-slate-800 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-200'
            }`}
          >
            Coordinator
          </button>
        </div>
      </div>
    </header>
  );
};
