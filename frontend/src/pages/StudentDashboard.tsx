import React, { useEffect, useState } from 'react';
import { 
  Award, BookOpen, AlertCircle, CheckCircle, Clock, 
  Calendar, MapPin, ArrowRight, Briefcase, FileText, CheckCircle2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { studentApi, applicationApi } from '../api/client';
import { DashboardData } from '../types';

interface StudentDashboardProps {
  onNavigateTab: (tab: string) => void;
}

export const StudentDashboard: React.FC<StudentDashboardProps> = ({ onNavigateTab }) => {
  const { student } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [applyingJobId, setApplyingJobId] = useState<number | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const loadDashboard = async () => {
    try {
      setIsLoading(true);
      const res = await studentApi.getDashboard();
      setData(res);
    } catch (err) {
      console.error("Failed to load dashboard", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, [student]);

  const handleApply = async (jobId: number) => {
    try {
      setApplyingJobId(jobId);
      await applicationApi.apply(jobId);
      setToastMessage("Successfully applied to drive!");
      await loadDashboard();
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || "Application failed.");
    } finally {
      setApplyingJobId(null);
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  if (isLoading || !data) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const stageDisplayList = [
    { key: 'APPLIED', label: 'Applied', color: 'bg-blue-50 text-blue-700 border-blue-200' },
    { key: 'SHORTLISTED', label: 'Shortlisted', color: 'bg-indigo-50 text-indigo-700 border-indigo-200' },
    { key: 'INTERVIEW_SCHEDULED', label: 'Interview Scheduled', color: 'bg-purple-50 text-purple-700 border-purple-200' },
    { key: 'INTERVIEWED', label: 'Interviewed', color: 'bg-amber-50 text-amber-700 border-amber-200' },
    { key: 'OFFERED', label: 'Offered', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
    { key: 'ACCEPTED', label: 'Accepted', color: 'bg-teal-50 text-teal-800 border-teal-300' },
  ];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-20 right-8 z-50 bg-slate-900 text-white px-5 py-3 rounded-xl shadow-xl flex items-center space-x-3 text-sm animate-in slide-in-from-top-4">
          <CheckCircle2 className="w-5 h-5 text-teal-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-navy-800 to-slate-900 text-white rounded-2xl p-6 sm:p-8 shadow-md relative overflow-hidden">
        <div className="relative z-10">
          <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/30 mb-3">
            Placement Season {data.active_season?.year || '2026-2027'} Active
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Welcome back, {data.student.full_name}! 👋
          </h2>
          <p className="text-slate-300 text-sm mt-1 max-w-2xl">
            Track your ongoing applications, review upcoming interview slots, and explore eligible company drives.
          </p>
        </div>
      </div>

      {/* Student Academic & Eligibility Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Cumulative CGPA</p>
            <p className="text-xl font-bold text-slate-800">{data.student.cgpa.toFixed(2)}</p>
            <span className="text-[11px] text-teal-600 font-medium">Out of 10.00</span>
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Branch</p>
            <p className="text-xl font-bold text-slate-800">{data.student.branch}</p>
            <span className="text-[11px] text-slate-400 font-medium">Accredited Dept</span>
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex items-center space-x-4">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${data.student.active_backlogs > 0 ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600'}`}>
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Active Backlogs</p>
            <p className="text-xl font-bold text-slate-800">{data.student.active_backlogs}</p>
            <span className={`text-[11px] font-medium ${data.student.active_backlogs > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
              {data.student.active_backlogs > 0 ? 'Rule limits apply' : 'Clean Academic Record'}
            </span>
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex items-center space-x-4">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${data.student.accepted_offer_this_season ? 'bg-teal-50 text-teal-600' : 'bg-slate-100 text-slate-400'}`}>
            <CheckCircle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Accepted Offer</p>
            <p className="text-xl font-bold text-slate-800">
              {data.student.accepted_offer_this_season ? 'Placed 🎉' : 'None'}
            </p>
            <span className="text-[11px] text-slate-500 font-medium">Max 1 / Season</span>
          </div>
        </div>
      </div>

      {/* Application Stage Distribution Cards */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold text-slate-800 text-base">Application Funnel Status</h3>
          <button 
            onClick={() => onNavigateTab('applications')}
            className="text-xs font-semibold text-teal-600 hover:text-teal-700 flex items-center space-x-1"
          >
            <span>View All Applications</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {stageDisplayList.map((st) => {
            const count = data.stage_counts[st.key] || 0;
            return (
              <div 
                key={st.key}
                onClick={() => onNavigateTab('applications')}
                className={`p-4 rounded-xl border transition-all cursor-pointer hover:shadow-md ${st.color}`}
              >
                <p className="text-xs font-semibold opacity-85 truncate">{st.label}</p>
                <p className="text-2xl font-black mt-2">{count}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Two Column Layout: Upcoming Interview & Open Drives */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Upcoming Interview */}
        <div className="lg:col-span-1 space-y-4">
          <h3 className="font-bold text-slate-800 text-base">Next Interview Slot</h3>
          
          {data.upcoming_interview ? (
            <div className="bg-white rounded-2xl p-6 border border-teal-200 shadow-sm relative overflow-hidden bg-gradient-to-br from-white to-teal-50/30">
              <div className="flex items-center justify-between mb-4">
                <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-teal-100 text-teal-800">
                  Round {data.upcoming_interview.round_number} Scheduled
                </span>
                <Clock className="w-4 h-4 text-teal-600" />
              </div>

              <h4 className="font-bold text-lg text-slate-900">{data.upcoming_interview.company_name}</h4>
              <p className="text-xs text-slate-500 mt-0.5">{data.upcoming_interview.job_title}</p>

              <div className="mt-4 pt-4 border-t border-slate-100 space-y-2 text-xs text-slate-600">
                <div className="flex items-center space-x-2">
                  <Calendar className="w-4 h-4 text-slate-400" />
                  <span className="font-medium text-slate-700">
                    {new Date(data.upcoming_interview.scheduled_time).toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <MapPin className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-700 truncate">{data.upcoming_interview.venue_or_link}</span>
                </div>
              </div>

              <button
                onClick={() => onNavigateTab('applications')}
                className="mt-5 w-full py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs rounded-xl transition-colors shadow-xs"
              >
                View Interview Details
              </button>
            </div>
          ) : (
            <div className="bg-white rounded-2xl p-8 border border-slate-200 text-center text-slate-400 space-y-3">
              <Calendar className="w-8 h-8 mx-auto text-slate-300" />
              <p className="text-xs font-medium">No upcoming interviews scheduled right now.</p>
            </div>
          )}
        </div>

        {/* Right Column: Open & Eligible Drives Preview */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-slate-800 text-base">Eligible Drives Open for You</h3>
            <button 
              onClick={() => onNavigateTab('drives')}
              className="text-xs font-semibold text-teal-600 hover:text-teal-700 flex items-center space-x-1"
            >
              <span>Explore All Drives</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs divide-y divide-slate-100">
            {data.eligible_drives.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                No active eligible drives found for your criteria.
              </div>
            ) : (
              data.eligible_drives.map((drive) => (
                <div key={drive.id} className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/60 transition-colors">
                  <div className="flex items-start space-x-3.5">
                    <div className="w-10 h-10 rounded-xl bg-slate-800 text-white font-bold flex items-center justify-center text-xs">
                      {drive.company_name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <h4 className="font-bold text-sm text-slate-800">{drive.title}</h4>
                      <p className="text-xs text-slate-500 font-medium">{drive.company_name} • Drive Date: {drive.drive_date}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4 self-end sm:self-center">
                    <div className="text-right">
                      <p className="text-sm font-bold text-teal-700">{drive.package_lpa} LPA</p>
                      <p className="text-[11px] text-slate-400 font-medium">Min CGPA {drive.min_cgpa.toFixed(1)}</p>
                    </div>

                    {drive.has_applied ? (
                      <span className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                        Applied
                      </span>
                    ) : (
                      <button
                        onClick={() => handleApply(drive.id)}
                        disabled={applyingJobId === drive.id}
                        className="px-4 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold transition-colors shadow-xs disabled:opacity-50"
                      >
                        {applyingJobId === drive.id ? 'Applying...' : 'Apply Now'}
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
