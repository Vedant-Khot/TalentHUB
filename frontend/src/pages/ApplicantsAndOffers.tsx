import React, { useEffect, useState } from 'react';
import { 
  Users, Search, Filter, Calendar, Award, Clock, 
  CheckCircle2, XCircle, Send, Check, AlertCircle, ChevronRight, X
} from 'lucide-react';
import { applicationApi, jobApi, interviewApi, offerApi } from '../api/client';
import { Application, JobListing, ApplicationStage, BranchName } from '../types';

export const ApplicantsAndOffers: React.FC = () => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Filters
  const [selectedJobId, setSelectedJobId] = useState<number | undefined>(undefined);
  const [selectedStage, setSelectedStage] = useState<string>('');
  const [selectedBranch, setSelectedBranch] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modals state
  const [scheduleModalApp, setScheduleModalApp] = useState<Application | null>(null);
  const [offerModalApp, setOfferModalApp] = useState<Application | null>(null);
  const [resultModalApp, setResultModalApp] = useState<Application | null>(null);

  // Modal Form Inputs
  const [roundNumber, setRoundNumber] = useState<number>(1);
  const [scheduledTime, setScheduledTime] = useState<string>('2026-10-25T10:00');
  const [venueOrLink, setVenueOrLink] = useState<string>('Placement Cell Interview Room 3 / Google Meet');
  const [interviewNotes, setInterviewNotes] = useState<string>('Technical problem-solving and systems interview.');
  const [offerPackage, setOfferPackage] = useState<number>(24.0);

  const fetchApplications = async () => {
    try {
      setIsLoading(true);
      const [apps, jobsList] = await Promise.all([
        applicationApi.listAll({
          jobId: selectedJobId,
          stage: selectedStage || undefined,
          branch: selectedBranch || undefined,
          search: searchQuery || undefined,
        }),
        jobApi.listJobs(false),
      ]);
      setApplications(apps);
      setJobs(jobsList);
    } catch (err) {
      console.error("Failed to load applicants", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, [selectedJobId, selectedStage, selectedBranch]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchApplications();
  };

  // 1. Action: Shortlist Applicant
  const handleShortlist = async (appId: number) => {
    try {
      await applicationApi.shortlist(appId);
      setToastMessage("Applicant successfully shortlisted!");
      await fetchApplications();
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || "Shortlisting failed.");
    } finally {
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  // 2. Action: Schedule Interview Round
  const handleScheduleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scheduleModalApp) return;
    try {
      await interviewApi.scheduleRound(scheduleModalApp.id, {
        round_number: Number(roundNumber),
        scheduled_time: new Date(scheduledTime).toISOString(),
        venue_or_link: venueOrLink.trim(),
        notes: interviewNotes.trim(),
      });
      setToastMessage(`Round ${roundNumber} interview scheduled successfully!`);
      setScheduleModalApp(null);
      await fetchApplications();
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || "Scheduling failed.");
    } finally {
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  // 3. Action: Mark Interview Complete
  const handleRecordResult = async (slotId: number, pass: boolean) => {
    try {
      await interviewApi.recordResult(slotId, pass ? 'PASSED' : 'FAILED', true);
      setToastMessage(pass ? "Round marked PASSED. Candidate moved to INTERVIEWED." : "Round marked FAILED.");
      setResultModalApp(null);
      await fetchApplications();
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || "Recording result failed.");
    } finally {
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  // 4. Action: Extend Offer
  const handleOfferSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!offerModalApp) return;
    try {
      await offerApi.createOffer(offerModalApp.id, Number(offerPackage));
      setToastMessage(`Offer of ${offerPackage} LPA extended successfully!`);
      setOfferModalApp(null);
      await fetchApplications();
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || "Offer release failed.");
    } finally {
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  const getStageBadgeColor = (stage: ApplicationStage) => {
    switch (stage) {
      case 'APPLIED': return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'SHORTLISTED': return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'INTERVIEW_SCHEDULED': return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'INTERVIEWED': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'OFFERED': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'ACCEPTED': return 'bg-teal-50 text-teal-800 border-teal-300 font-bold';
      default: return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-20 right-8 z-50 bg-slate-900 text-white px-5 py-3 rounded-xl shadow-xl flex items-center space-x-3 text-sm animate-in slide-in-from-top-4">
          <CheckCircle2 className="w-5 h-5 text-teal-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-800">Applicants & Offer Management</h2>
        <p className="text-xs text-slate-500 mt-1">
          Review candidates, shortlist applications, coordinate interview rounds, and extend job offers.
        </p>
      </div>

      {/* Filters & Search Bar */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by student or USN..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
          />
        </form>

        <div className="flex flex-wrap items-center gap-3">
          {/* Drive Filter */}
          <select
            value={selectedJobId || ''}
            onChange={(e) => setSelectedJobId(e.target.value ? Number(e.target.value) : undefined)}
            className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:outline-none focus:border-teal-500"
          >
            <option value="">All Job Drives</option>
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.company_name} - {j.title}
              </option>
            ))}
          </select>

          {/* Stage Filter */}
          <select
            value={selectedStage}
            onChange={(e) => setSelectedStage(e.target.value)}
            className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:outline-none focus:border-teal-500"
          >
            <option value="">All Stages</option>
            <option value="APPLIED">Applied</option>
            <option value="SHORTLISTED">Shortlisted</option>
            <option value="INTERVIEW_SCHEDULED">Interview Scheduled</option>
            <option value="INTERVIEWED">Interviewed</option>
            <option value="OFFERED">Offered</option>
            <option value="ACCEPTED">Accepted</option>
          </select>

          {/* Branch Filter */}
          <select
            value={selectedBranch}
            onChange={(e) => setSelectedBranch(e.target.value)}
            className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:outline-none focus:border-teal-500"
          >
            <option value="">All Branches</option>
            <option value="CSE">CSE</option>
            <option value="ECE">ECE</option>
            <option value="ISE">ISE</option>
            <option value="MECH">MECH</option>
            <option value="CIVIL">CIVIL</option>
          </select>
        </div>
      </div>

      {/* Applicants Table */}
      {isLoading ? (
        <div className="p-16 flex items-center justify-center">
          <div className="w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : applications.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 border border-slate-200 text-center text-slate-400 space-y-3">
          <Users className="w-10 h-10 mx-auto text-slate-300" />
          <p className="text-sm font-medium">No applicants found matching the filters.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <th className="py-3.5 px-6">Candidate</th>
                  <th className="py-3.5 px-4">Academic Details</th>
                  <th className="py-3.5 px-4">Applied Drive</th>
                  <th className="py-3.5 px-4">Current Stage</th>
                  <th className="py-3.5 px-4">Offer Status</th>
                  <th className="py-3.5 px-6 text-right">Workflow Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {applications.map((app) => {
                  const isApplied = app.stage === 'APPLIED';
                  const isShortlisted = app.stage === 'SHORTLISTED';
                  const isInterviewScheduled = app.stage === 'INTERVIEW_SCHEDULED';
                  const isInterviewed = app.stage === 'INTERVIEWED';
                  const isOffered = app.stage === 'OFFERED';
                  const isAccepted = app.stage === 'ACCEPTED';
                  const activeSlot = app.interviews.find((s) => s.status === 'SCHEDULED' || s.status === 'RESCHEDULED');

                  return (
                    <tr key={app.id} className="hover:bg-slate-50/70 transition-colors">
                      {/* Candidate */}
                      <td className="py-4 px-6">
                        <div className="flex items-center space-x-3">
                          <div className="w-9 h-9 rounded-full bg-slate-900 text-white font-bold flex items-center justify-center text-xs">
                            {app.student_name.charAt(0)}
                          </div>
                          <div>
                            <p className="font-bold text-slate-900">{app.student_name}</p>
                            <p className="text-[11px] text-slate-500 font-medium">{app.student_usn}</p>
                          </div>
                        </div>
                      </td>

                      {/* Academic Details */}
                      <td className="py-4 px-4">
                        <span className="font-bold text-slate-800">{app.student_branch}</span>
                        <p className="text-[11px] text-slate-500">CGPA: {app.student_cgpa.toFixed(2)}</p>
                      </td>

                      {/* Applied Drive */}
                      <td className="py-4 px-4">
                        <p className="font-bold text-slate-800">{app.job_title}</p>
                        <p className="text-[11px] text-slate-500">{app.company_name} • {app.package_lpa} LPA</p>
                      </td>

                      {/* Stage Badge */}
                      <td className="py-4 px-4">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${getStageBadgeColor(app.stage)}`}>
                          {app.stage}
                        </span>
                      </td>

                      {/* Offer Status */}
                      <td className="py-4 px-4">
                        {app.offer ? (
                          <div>
                            <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                              app.offer.status === 'ACCEPTED' 
                                ? 'bg-teal-100 text-teal-800' 
                                : app.offer.status === 'DECLINED'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-amber-100 text-amber-800'
                            }`}>
                              {app.offer.status}: {app.offer.package_lpa} LPA
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400 text-[11px]">No offer</span>
                        )}
                      </td>

                      {/* Action Button */}
                      <td className="py-4 px-6 text-right">
                        {isApplied && (
                          <button
                            onClick={() => handleShortlist(app.id)}
                            className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold transition-colors shadow-2xs"
                          >
                            Shortlist
                          </button>
                        )}

                        {isShortlisted && (
                          <button
                            onClick={() => {
                              setScheduleModalApp(app);
                              setRoundNumber(app.interviews.length + 1);
                            }}
                            className="px-3.5 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-semibold transition-colors shadow-2xs"
                          >
                            Schedule Round {app.interviews.length + 1}
                          </button>
                        )}

                        {isInterviewScheduled && activeSlot && (
                          <button
                            onClick={() => setResultModalApp(app)}
                            className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold transition-colors shadow-2xs"
                          >
                            Record Result
                          </button>
                        )}

                        {isInterviewed && (
                          <button
                            onClick={() => {
                              setOfferModalApp(app);
                              setOfferPackage(app.package_lpa);
                            }}
                            className="px-3.5 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold transition-colors shadow-2xs"
                          >
                            Extend Offer
                          </button>
                        )}

                        {(isOffered || isAccepted) && (
                          <span className="text-[11px] font-semibold text-slate-500">
                            {isAccepted ? 'Placed' : 'Offer Pending'}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal 1: Schedule Interview Round */}
      {scheduleModalApp && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-base">Schedule Interview Round</h3>
              <button onClick={() => setScheduleModalApp(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleScheduleSubmit} className="py-4 space-y-4">
              <p className="text-xs text-slate-600">
                Candidate: <span className="font-bold text-slate-800">{scheduleModalApp.student_name}</span> ({scheduleModalApp.student_usn})
              </p>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Round Number</label>
                <input
                  type="number"
                  min="1"
                  value={roundNumber}
                  onChange={(e) => setRoundNumber(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Scheduled Date & Time</label>
                <input
                  type="datetime-local"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Venue or Meeting Link</label>
                <input
                  type="text"
                  value={venueOrLink}
                  onChange={(e) => setVenueOrLink(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Notes / Instructions</label>
                <textarea
                  rows={2}
                  value={interviewNotes}
                  onChange={(e) => setInterviewNotes(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setScheduleModalApp(null)}
                  className="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold shadow-xs"
                >
                  Schedule Round
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 2: Record Interview Result */}
      {resultModalApp && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-base">Record Interview Outcome</h3>
              <button onClick={() => setResultModalApp(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="py-4 space-y-4">
              <p className="text-xs text-slate-600">
                Evaluating candidate: <span className="font-bold text-slate-800">{resultModalApp.student_name}</span>
              </p>

              <p className="text-xs text-slate-500">
                Marking the round as PASSED and concluding rounds moves the application to <strong>INTERVIEWED</strong>, enabling offer extension.
              </p>

              <div className="pt-3 flex items-center justify-end space-x-3">
                <button
                  onClick={() => {
                    const slot = resultModalApp.interviews.find((s) => s.status === 'SCHEDULED' || s.status === 'RESCHEDULED');
                    if (slot) handleRecordResult(slot.id, false);
                  }}
                  className="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-800 rounded-xl text-xs font-semibold"
                >
                  Mark FAILED
                </button>
                <button
                  onClick={() => {
                    const slot = resultModalApp.interviews.find((s) => s.status === 'SCHEDULED' || s.status === 'RESCHEDULED');
                    if (slot) handleRecordResult(slot.id, true);
                  }}
                  className="px-5 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold shadow-xs"
                >
                  Mark PASSED & Conclude
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal 3: Extend Offer */}
      {offerModalApp && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-base">Extend Placement Offer</h3>
              <button onClick={() => setOfferModalApp(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleOfferSubmit} className="py-4 space-y-4">
              <p className="text-xs text-slate-600">
                Candidate: <span className="font-bold text-slate-800">{offerModalApp.student_name}</span> ({offerModalApp.job_title})
              </p>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Offered Package (LPA)</label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  value={offerPackage}
                  onChange={(e) => setOfferPackage(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 font-bold"
                />
              </div>

              <div className="p-3 bg-teal-50 border border-teal-200 rounded-xl text-xs text-teal-800">
                Extending this offer will automatically generate a private encrypted PDF offer letter in local storage and notify the candidate.
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setOfferModalApp(null)}
                  className="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold shadow-xs"
                >
                  Extend Official Offer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
