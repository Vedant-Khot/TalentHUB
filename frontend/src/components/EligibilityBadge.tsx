import React, { useState } from 'react';
import { CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';
import { EligibilityCheckResult } from '../types';

interface EligibilityBadgeProps {
  eligibility?: EligibilityCheckResult | null;
}

export const EligibilityBadge: React.FC<EligibilityBadgeProps> = ({ eligibility }) => {
  const [showModal, setShowModal] = useState(false);

  if (!eligibility) {
    return (
      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
        Eligibility Pending
      </span>
    );
  }

  return (
    <>
      {eligibility.is_eligible ? (
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-50 text-teal-700 border border-teal-200">
          <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-teal-600" />
          Eligible to Apply
        </span>
      ) : (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setShowModal(true);
          }}
          className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100 transition-colors cursor-pointer"
        >
          <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-600" />
          Ineligible (View Reason)
        </button>
      )}

      {/* Explanatory Reasons Modal */}
      {showModal && (
        <div 
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-200"
          onClick={() => setShowModal(false)}
        >
          <div 
            className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center space-x-2 text-amber-800 font-bold">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
                <h3>Eligibility Assessment Details</h3>
              </div>
              <button 
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-600 rounded-lg p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="py-4 space-y-3">
              <p className="text-xs text-slate-500">
                TalentHub evaluated your profile against this drive's criteria using deterministic placement rules:
              </p>

              <div className="bg-amber-50/70 border border-amber-200/80 rounded-xl p-3.5 space-y-2">
                <h4 className="text-xs font-semibold text-amber-900 uppercase tracking-wider">Unsatisfied Criteria</h4>
                <ul className="space-y-1.5 text-xs text-amber-900">
                  {eligibility.rejection_reasons.map((r, i) => (
                    <li key={i} className="flex items-start">
                      <span className="text-amber-600 mr-2 font-bold">•</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Individual Rule Breakdown */}
              <div className="bg-slate-50 rounded-xl p-3.5 space-y-2 border border-slate-200">
                <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Evaluation Rules</h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex items-center justify-between p-1.5 bg-white rounded border border-slate-200">
                    <span className="text-slate-600">Min CGPA</span>
                    <span className={`font-semibold ${eligibility.cgpa_pass ? 'text-teal-600' : 'text-red-600'}`}>
                      {eligibility.cgpa_pass ? 'PASS' : 'FAIL'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-1.5 bg-white rounded border border-slate-200">
                    <span className="text-slate-600">Backlogs</span>
                    <span className={`font-semibold ${eligibility.backlogs_pass ? 'text-teal-600' : 'text-red-600'}`}>
                      {eligibility.backlogs_pass ? 'PASS' : 'FAIL'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-1.5 bg-white rounded border border-slate-200">
                    <span className="text-slate-600">Season Offer</span>
                    <span className={`font-semibold ${eligibility.season_offer_pass ? 'text-teal-600' : 'text-red-600'}`}>
                      {eligibility.season_offer_pass ? 'PASS' : 'FAIL'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-1.5 bg-white rounded border border-slate-200">
                    <span className="text-slate-600">Branch</span>
                    <span className={`font-semibold ${eligibility.branch_pass ? 'text-teal-600' : 'text-red-600'}`}>
                      {eligibility.branch_pass ? 'PASS' : 'FAIL'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 bg-slate-800 text-white rounded-lg text-xs font-semibold hover:bg-slate-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
