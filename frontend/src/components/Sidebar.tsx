import React from 'react';
import { 
  GraduationCap, LayoutDashboard, Briefcase, FileText, 
  PlusCircle, Users, LogOut, CheckCircle2, Building2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, setCurrentTab }) => {
  const { user, student, logout } = useAuth();
  const isCoordinator = user?.role === 'PLACEMENT_COORDINATOR';

  const studentNavItems = [
    { id: 'dashboard', label: 'Student Dashboard', icon: LayoutDashboard },
    { id: 'drives', label: 'Job Drives', icon: Briefcase },
    { id: 'applications', label: 'My Applications', icon: FileText },
  ];

  const coordinatorNavItems = [
    { id: 'coordinator-dashboard', label: 'Overview & Analytics', icon: LayoutDashboard },
    { id: 'post-drive', label: 'Post a Drive', icon: PlusCircle },
    { id: 'applicants', label: 'Applicants & Offers', icon: Users },
  ];

  const navItems = isCoordinator ? coordinatorNavItems : studentNavItems;

  return (
    <aside className="w-64 bg-[#0F172A] text-slate-200 flex flex-col h-screen sticky top-0 border-r border-slate-800 select-none">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800 flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-teal-600 flex items-center justify-center text-white shadow-lg shadow-teal-600/30">
          <GraduationCap className="w-6 h-6" />
        </div>
        <div>
          <h1 className="font-bold text-lg text-white tracking-wide">TalentHub</h1>
          <p className="text-xs text-slate-400 font-medium">Campus Placement Portal</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          {isCoordinator ? 'Coordinator Management' : 'Student Portal'}
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setCurrentTab(item.id)}
              className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-teal-600 text-white shadow-sm shadow-teal-600/30'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Icon className={`w-4.5 h-4.5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* User Information & Sign Out */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/50">
        <div className="flex items-center space-x-3 mb-3 px-1">
          <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-teal-400 font-bold text-sm">
            {isCoordinator ? 'PC' : (student?.full_name?.charAt(0) || 'ST')}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-white truncate">
              {isCoordinator ? 'Placement Admin' : (student?.full_name || user?.email)}
            </p>
            <p className="text-xs text-slate-400 truncate">
              {isCoordinator ? 'Coordinator' : `${student?.usn || ''} • ${student?.branch || ''}`}
            </p>
          </div>
        </div>

        <button
          onClick={logout}
          className="w-full flex items-center justify-center space-x-2 px-3 py-2 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors border border-slate-800"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
