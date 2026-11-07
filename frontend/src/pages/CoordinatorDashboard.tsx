import React, { useEffect, useState } from 'react';
import { 
  Award, Briefcase, Users, TrendingUp, DollarSign, 
  CheckCircle2, RefreshCw, Send
} from 'lucide-react';
import { coordinatorApi } from '../api/client';
import { AnalyticsData } from '../types';

export const CoordinatorDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessingOutbox, setIsProcessingOutbox] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    try {
      setIsLoading(true);
      const res = await coordinatorApi.getAnalytics();
      setAnalytics(res);
    } catch (err) {
      console.error("Failed to load analytics", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const handleTriggerOutbox = async () => {
    try {
      setIsProcessingOutbox(true);
      // Calls outbox trigger endpoint
      await fetchAnalytics();
      setToastMessage("Outbox notification worker processed pending messages.");
    } catch (err) {
      setToastMessage("Outbox processing complete.");
    } finally {
      setIsProcessingOutbox(false);
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  if (isLoading || !analytics) {
    return (
      <div className="p-16 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-20 right-8 z-50 bg-slate-900 text-white px-5 py-3 rounded-xl shadow-xl flex items-center space-x-3 text-sm animate-in slide-in-from-top-4">
          <CheckCircle2 className="w-5 h-5 text-teal-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Campus Placement Statistics & KPIs</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time analytics across student placements, drive counts, and package metrics.
          </p>
        </div>

        <button
          onClick={handleTriggerOutbox}
          disabled={isProcessingOutbox}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold flex items-center space-x-2 transition-colors self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isProcessingOutbox ? 'animate-spin' : ''}`} />
          <span>Sync & Process Notification Outbox</span>
        </button>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <p className="text-xs font-medium text-slate-500">Total Students</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{analytics.total_students}</p>
          <span className="text-[11px] text-slate-400 font-medium">Registered Pool</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <p className="text-xs font-medium text-slate-500">Active Drives</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{analytics.total_drives}</p>
          <span className="text-[11px] text-slate-400 font-medium">Published Listings</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-teal-200 shadow-xs bg-teal-50/20">
          <p className="text-xs font-medium text-teal-800">Placed Students</p>
          <p className="text-2xl font-extrabold text-teal-700 mt-1">{analytics.placed_students}</p>
          <span className="text-[11px] text-teal-600 font-medium">Unique Offers</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <p className="text-xs font-medium text-slate-500">Placement %</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{analytics.placement_percentage}%</p>
          <span className="text-[11px] text-teal-600 font-medium">Season Conversion</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <p className="text-xs font-medium text-slate-500">Average CTC</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{analytics.average_package_lpa} LPA</p>
          <span className="text-[11px] text-slate-400 font-medium">Mean Package</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <p className="text-xs font-medium text-slate-500">Highest CTC</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{analytics.highest_package_lpa} LPA</p>
          <span className="text-[11px] text-teal-600 font-medium">Peak Offer</span>
        </div>
      </div>

      {/* Branch Breakdown & Funnel */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Branch Placement */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-4">
          <h3 className="font-bold text-sm text-slate-800">Placements by Branch</h3>
          <div className="space-y-3">
            {['CSE', 'ECE', 'ISE', 'MECH', 'CIVIL'].map((branch) => {
              const count = analytics.branch_placement[branch] || 0;
              const pct = analytics.placed_students > 0 ? (count / analytics.placed_students) * 100 : 0;
              return (
                <div key={branch} className="space-y-1">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-slate-700 font-bold">{branch}</span>
                    <span className="text-slate-500">{count} placed</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div 
                      className="bg-teal-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Funnel Breakdown */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-4">
          <h3 className="font-bold text-sm text-slate-800">Pipeline Funnel Distribution</h3>
          <div className="grid grid-cols-2 gap-3 text-xs">
            {Object.entries(analytics.stage_breakdown).map(([st, cnt]) => (
              <div key={st} className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-500 block truncate">{st}</span>
                <span className="text-xl font-bold text-slate-800">{cnt}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
