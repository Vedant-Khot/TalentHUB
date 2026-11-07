import React, { useEffect, useState } from 'react';
import { 
  FileText, Calendar, Clock, MapPin, Download, CheckCircle, 
  XCircle, AlertCircle, Building2, ExternalLink, CheckCircle2 
} from 'lucide-react';
import { applicationApi, offerApi } from '../api/client';
import { Application } from '../types';
import { StageStepper } from '../components/StageStepper';

export const MyApplications: React.FC = () => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [respondingOfferId, setRespondingOfferId] = useState<number | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const fetchApplications = async () => {
    try {
      setIsLoading(true);
      const res = await applicationApi.getMyApplications();
      setApplications(res);
    } catch (err) {
      console.error("Failed to load applications", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const handleOfferResponse = async (offerId: number, action: 'ACCEPT' | 'DECLINE') => {
    try {
      setRespondingOfferId(offerId);
      await offerApi.respond(offerId, action);
      setToastMessage(action === 'ACCEPT' ? "🎉 Offer accepted successfully! Congratulations!" : "Offer declined.");
      await fetchApplications();
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || "Action failed.");
    } finally {
      setRespondingOfferId(null);
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  const handleDownloadLetter = (offerId: number) => {
    const token = localStorage.getItem('talenthub_token');
    window.open(`${offerApi.downloadLetterUrl(offerId)}?token=${token}`, '_blank');
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
        <h2 className="text-xl font-bold text-slate-800">My Applications & Placement Progress</h2>
        <p className="text-xs text-slate-500 mt-1">
          Monitor your interview schedules, track stage progression, and manage extended offers.
        </p>
      </div>

      {isLoading ? (
        <div className="p-16 flex items-center justify-center">
          <div className="w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : applications.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 border border-slate-200 text-center text-slate-400 space-y-3">
          <FileText className="w-10 h-10 mx-auto text-slate-300" />
          <p className="text-sm font-medium">You have not submitted any applications yet.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {applications.map((app) => {
            const hasPendingOffer = app.offer && app.offer.status === 'PENDING';
            const isOfferAccepted = app.offer && app.offer.status === 'ACCEPTED';
            const isOfferDeclined = app.offer && app.offer.status === 'DECLINED';
            const scheduledSlot = app.interviews.find((s) => s.status === 'SCHEDULED' || s.status === 'RESCHEDULED');

            return (
              <div 
                key={app.id} 
                className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden transition-all hover:border-slate-300"
              >
                {/* Application Header Bar */}
                <div className="p-6 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-50/50">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 rounded-xl bg-slate-900 text-white font-extrabold flex items-center justify-center text-sm shadow-xs">
                      {app.company_name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="font-bold text-base text-slate-900">{app.job_title}</h3>
                      <p className="text-xs text-slate-500 font-medium">
                        {app.company_name} • Applied on {new Date(app.applied_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3 self-end sm:self-center">
                    <span className="text-xs font-semibold text-slate-500">Package:</span>
                    <span className="text-base font-extrabold text-teal-700">{app.package_lpa} LPA</span>
                  </div>
                </div>

                {/* 6-Stage Horizontal Progress Stepper */}
                <div className="px-6 py-4 bg-white border-b border-slate-100">
                  <StageStepper currentStage={app.stage} />
                </div>

                {/* Details Section: Upcoming Interview & Offer Details */}
                <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-5">
                  {/* Interview Information Card */}
                  <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/80 space-y-3">
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-2">
                      <Clock className="w-4 h-4 text-teal-600" />
                      <span>Interview Round Details</span>
                    </h4>

                    {scheduledSlot ? (
                      <div className="space-y-2 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">Round Number:</span>
                          <span className="font-bold text-slate-800">Round {scheduledSlot.round_number}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">Scheduled Date & Time:</span>
                          <span className="font-bold text-slate-800">
                            {new Date(scheduledSlot.scheduled_time).toLocaleString()}
                          </span>
                        </div>
                        <div className="flex items-start justify-between">
                          <span className="text-slate-500">Venue / Meeting:</span>
                          <span className="font-semibold text-slate-800 text-right max-w-[200px] truncate">
                            {scheduledSlot.venue_or_link}
                          </span>
                        </div>
                        {scheduledSlot.notes && (
                          <p className="text-[11px] text-slate-500 bg-white p-2 rounded border border-slate-200 mt-2">
                            Note: {scheduledSlot.notes}
                          </p>
                        )}
                      </div>
                    ) : app.interviews.length > 0 ? (
                      <p className="text-xs text-slate-500">
                        Completed {app.interviews.length} round(s). Next schedule pending coordinator update.
                      </p>
                    ) : (
                      <p className="text-xs text-slate-400">
                        No interview slot scheduled yet for this application.
                      </p>
                    )}
                  </div>

                  {/* Offer Information & Response Card */}
                  <div className={`rounded-xl p-4 border space-y-3 ${
                    app.offer 
                      ? 'bg-teal-50/50 border-teal-200' 
                      : 'bg-slate-50 border-slate-200/80'
                  }`}>
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-teal-600" />
                      <span>Offer Status</span>
                    </h4>

                    {app.offer ? (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-600">Offered CTC:</span>
                          <span className="text-base font-extrabold text-teal-700">{app.offer.package_lpa} LPA</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-600">Status:</span>
                          <span className={`font-bold px-2 py-0.5 rounded text-xs ${
                            isOfferAccepted 
                              ? 'bg-teal-200/60 text-teal-800' 
                              : isOfferDeclined
                              ? 'bg-red-100 text-red-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}>
                            {app.offer.status}
                          </span>
                        </div>

                        {/* Download Letter Button */}
                        <button
                          onClick={() => handleDownloadLetter(app.offer!.id)}
                          className="w-full flex items-center justify-center space-x-2 py-2 px-3 bg-white hover:bg-slate-50 border border-teal-300 rounded-lg text-xs font-semibold text-teal-800 transition-colors shadow-2xs"
                        >
                          <Download className="w-3.5 h-3.5 text-teal-600" />
                          <span>Download Confidential Offer Letter (.PDF)</span>
                        </button>

                        {/* Accept / Decline actions if pending */}
                        {hasPendingOffer && (
                          <div className="pt-2 flex items-center space-x-2">
                            <button
                              onClick={() => handleOfferResponse(app.offer!.id, 'ACCEPT')}
                              disabled={respondingOfferId === app.offer!.id}
                              className="flex-1 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-bold transition-all shadow-xs"
                            >
                              {respondingOfferId === app.offer!.id ? 'Processing...' : 'Accept Offer'}
                            </button>
                            <button
                              onClick={() => handleOfferResponse(app.offer!.id, 'DECLINE')}
                              disabled={respondingOfferId === app.offer!.id}
                              className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-xs font-semibold transition-all"
                            >
                              Decline
                            </button>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400">
                        Offers are extended following successful interview rounds.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
