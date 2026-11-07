import React, { useEffect, useState } from 'react';
import { 
  Briefcase, Search, Filter, Calendar, Award, 
  AlertCircle, CheckCircle2, ChevronRight, Check, X, ShieldCheck, FileText, Send
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { jobApi, applicationApi } from '../api/client';
import { JobListing } from '../types';
import { EligibilityBadge } from '../components/EligibilityBadge';

export const JobDrives: React.FC = () => {
  const { student, user } = useAuth();
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [eligibleOnly, setEligibleOnly] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [applyingJobId, setApplyingJobId] = useState<number | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [applyModalJob, setApplyModalJob] = useState<JobListing | null>(null);
  const [coverNote, setCoverNote] = useState<string>('');
  const [confirmConsent, setConfirmConsent] = useState<boolean>(true);

  const fetchJobs = async () => {
    try {
      setIsLoading(true);
      const res = await jobApi.listJobs(eligibleOnly);
      setJobs(res);
    } catch (err) {
      console.error("Failed to load jobs", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [eligibleOnly, user]);

  const handleOpenApplyModal = (job: JobListing) => {
    setApplyModalJob(job);
    setCoverNote('I am interested in this role and excited to contribute to the engineering team.');
    setConfirmConsent(true);
  };

  const handleConfirmSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!applyModalJob) return;
    if (!confirmConsent) {
      setToastMessage("Please confirm academic data processing consent to proceed.");
      return;
    }

    try {
      setApplyingJobId(applyModalJob.id);
      await applicationApi.apply(applyModalJob.id);
      setToastMessage(`🎉 Application to ${applyModalJob.company_name} submitted successfully!`);
      setApplyModalJob(null);
      await fetchJobs();
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || "Application submission failed.");
    } finally {
      setApplyingJobId(null);
      setTimeout(() => setToastMessage(null), 5000);
    }
  };

  const filteredJobs = jobs.filter((job) => {
    const term = searchTerm.toLowerCase();
    return (
      job.title.toLowerCase().includes(term) ||
      job.company_name.toLowerCase().includes(term)
    );
  });

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-20 right-8 z-50 bg-slate-900 text-white px-5 py-3 rounded-xl shadow-xl flex items-center space-x-3 text-sm animate-in slide-in-from-top-4">
          <CheckCircle2 className="w-5 h-5 text-teal-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Student Profile Evaluation Header Banner */}
      {student && (
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700 font-bold">
              {student.branch}
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium">Evaluation Profile</p>
              <h3 className="text-sm font-bold text-slate-900">
                {student.full_name} • CGPA {student.cgpa.toFixed(2)} • {student.active_backlogs} Active Backlog(s)
              </h3>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs text-slate-600 bg-slate-50 px-4 py-2 rounded-xl border border-slate-200">
            <span>Eligible offers accepted this season:</span>
            <span className={`font-bold ${student.accepted_offer_this_season ? 'text-teal-600' : 'text-slate-700'}`}>
              {student.accepted_offer_this_season ? '1 (Accepted)' : '0'}
            </span>
          </div>
        </div>
      )}

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by company or role..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
          />
        </div>

        {/* Eligible Only Toggle */}
        <div className="flex items-center space-x-3 self-end sm:self-center">
          <label className="flex items-center space-x-2 text-xs font-semibold text-slate-700 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={eligibleOnly}
              onChange={(e) => setEligibleOnly(e.target.checked)}
              className="w-4 h-4 text-teal-600 rounded border-slate-300 focus:ring-teal-500 cursor-pointer"
            />
            <span>Show Eligible Drives Only</span>
          </label>
        </div>
      </div>

      {/* Job Drives Cards Grid */}
      {isLoading ? (
        <div className="p-16 flex items-center justify-center">
          <div className="w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filteredJobs.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 border border-slate-200 text-center text-slate-400 space-y-3">
          <Briefcase className="w-10 h-10 mx-auto text-slate-300" />
          <p className="text-sm font-medium">No campus drives match the selected criteria.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filteredJobs.map((job) => {
            const isEligible = job.eligibility?.is_eligible ?? true;

            return (
              <div 
                key={job.id}
                className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs hover:shadow-md transition-all flex flex-col justify-between space-y-5"
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center space-x-3.5">
                      <div className="w-12 h-12 rounded-xl bg-slate-900 text-white font-extrabold flex items-center justify-center text-sm shadow-xs">
                        {job.company_name.slice(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <h3 className="font-bold text-base text-slate-900">{job.title}</h3>
                        <p className="text-xs font-medium text-slate-500">{job.company_name}</p>
                      </div>
                    </div>

                    <div className="text-right">
                      <span className="text-base font-extrabold text-teal-700">{job.package_lpa} LPA</span>
                      <p className="text-[11px] text-slate-400 font-medium">Annual CTC</p>
                    </div>
                  </div>

                  {/* Description Snippet */}
                  <p className="mt-3 text-xs text-slate-600 line-clamp-2 leading-relaxed">
                    {job.description}
                  </p>

                  {/* Criteria Grid */}
                  <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-3 gap-2 text-[11px]">
                    <div className="bg-slate-50 p-2 rounded-lg border border-slate-200/60">
                      <span className="text-slate-400 block">Min CGPA</span>
                      <span className="font-bold text-slate-800">{job.min_cgpa.toFixed(1)} / 10</span>
                    </div>
                    <div className="bg-slate-50 p-2 rounded-lg border border-slate-200/60">
                      <span className="text-slate-400 block">Max Backlogs</span>
                      <span className="font-bold text-slate-800">{job.max_backlogs} allowed</span>
                    </div>
                    <div className="bg-slate-50 p-2 rounded-lg border border-slate-200/60">
                      <span className="text-slate-400 block">Drive Date</span>
                      <span className="font-bold text-slate-800">{job.drive_date}</span>
                    </div>
                  </div>

                  {/* Allowed Branches */}
                  <div className="mt-3 flex items-center space-x-1.5 flex-wrap gap-y-1">
                    <span className="text-[11px] text-slate-400 font-medium mr-1">Branches:</span>
                    {job.is_open_to_all_branches ? (
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700">
                        Open to All Branches
                      </span>
                    ) : (
                      job.allowed_branches.map((b) => (
                        <span key={b} className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">
                          {b}
                        </span>
                      ))
                    )}
                  </div>
                </div>

                {/* Card Footer: Eligibility status and action button */}
                <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-4">
                  <div>
                    {job.has_applied ? (
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                        <Check className="w-3.5 h-3.5 mr-1" />
                        Stage: {job.application_stage}
                      </span>
                    ) : (
                      <EligibilityBadge eligibility={job.eligibility} />
                    )}
                  </div>

                  <div>
                    {job.has_applied ? (
                      <span className="text-xs font-semibold text-slate-400">Application Submitted</span>
                    ) : (
                      <button
                        onClick={() => handleOpenApplyModal(job)}
                        disabled={!isEligible || applyingJobId === job.id}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-xs ${
                          isEligible
                            ? 'bg-teal-600 hover:bg-teal-700 text-white cursor-pointer active:scale-95'
                            : 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200'
                        }`}
                      >
                        Apply Now
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Interactive Application Modal */}
      {applyModalJob && (
        <div 
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-200"
          onClick={() => setApplyModalJob(null)}
        >
          <div 
            className="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-7 shadow-2xl border border-slate-200 space-y-5"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-slate-900 text-white font-extrabold flex items-center justify-center text-xs">
                  {applyModalJob.company_name.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <h3 className="font-bold text-base text-slate-900">{applyModalJob.title}</h3>
                  <p className="text-xs text-slate-500 font-medium">{applyModalJob.company_name} • {applyModalJob.package_lpa} LPA</p>
                </div>
              </div>
              <button 
                onClick={() => setApplyModalJob(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Candidate Evaluation Summary */}
            {student && (
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-2">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Your Candidate Profile</h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Applicant Name</span>
                    <span className="font-bold text-slate-800">{student.full_name}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">University Seat No (USN)</span>
                    <span className="font-bold text-slate-800">{student.usn}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Academic Branch</span>
                    <span className="font-bold text-slate-800">{student.branch}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Cumulative CGPA</span>
                    <span className="font-bold text-teal-700">{student.cgpa.toFixed(2)} (Min required: {applyModalJob.min_cgpa.toFixed(1)})</span>
                  </div>
                </div>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleConfirmSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Candidate Statement / Note to Recruiter (Optional)
                </label>
                <textarea
                  rows={3}
                  value={coverNote}
                  onChange={(e) => setCoverNote(e.target.value)}
                  placeholder="Share a brief statement or note regarding your preparation and interest in this role..."
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                />
              </div>

              {/* Mandatory Consent Checkbox */}
              <div className="bg-teal-50/60 border border-teal-200 rounded-xl p-3.5 flex items-start space-x-3">
                <input
                  type="checkbox"
                  id="consentCheckbox"
                  checked={confirmConsent}
                  onChange={(e) => setConfirmConsent(e.target.checked)}
                  className="mt-0.5 w-4 h-4 text-teal-600 rounded border-slate-300 focus:ring-teal-500 cursor-pointer"
                />
                <label htmlFor="consentCheckbox" className="text-xs text-slate-700 cursor-pointer leading-relaxed">
                  I confirm that my academic CGPA, branch, and backlog details are accurate, and I grant permission to share my placement dossier with <strong>{applyModalJob.company_name}</strong> for this campus recruitment drive.
                </label>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setApplyModalJob(null)}
                  className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={applyingJobId === applyModalJob.id || !confirmConsent}
                  className="px-6 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs flex items-center space-x-2 disabled:opacity-50 cursor-pointer"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{applyingJobId === applyModalJob.id ? 'Submitting...' : 'Confirm & Submit Application'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
