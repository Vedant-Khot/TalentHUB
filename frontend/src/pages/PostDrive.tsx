import React, { useEffect, useState } from 'react';
import { 
  PlusCircle, Building2, Calendar, Award, AlertCircle, 
  Eye, CheckCircle2, Save, Send
} from 'lucide-react';
import { coordinatorApi, jobApi } from '../api/client';
import { Company, PlacementSeason, BranchName } from '../types';

export const PostDrive: React.FC = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [seasons, setSeasons] = useState<PlacementSeason[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Form State
  const [companyId, setCompanyId] = useState<number>(0);
  const [newCompanyName, setNewCompanyName] = useState<string>('');
  const [isCreatingCompany, setIsCreatingCompany] = useState<boolean>(false);
  const [seasonId, setSeasonId] = useState<number>(0);
  const [title, setTitle] = useState<string>('Software Development Engineer');
  const [description, setDescription] = useState<string>('Join our core product engineering team to build scalable systems.');
  const [packageLpa, setPackageLpa] = useState<number>(22.0);
  const [minCgpa, setMinCgpa] = useState<number>(7.5);
  const [maxBacklogs, setMaxBacklogs] = useState<number>(0);
  const [driveDate, setDriveDate] = useState<string>('2026-11-15');
  const [deadline, setDeadline] = useState<string>('2026-11-10');
  const [selectedBranches, setSelectedBranches] = useState<BranchName[]>(['CSE', 'ECE', 'ISE']);

  const branchesList: BranchName[] = ['CSE', 'ECE', 'ISE', 'MECH', 'CIVIL'];

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        const [comps, seas] = await Promise.all([
          coordinatorApi.listCompanies(),
          coordinatorApi.listSeasons(),
        ]);
        setCompanies(comps);
        setSeasons(seas);
        if (comps.length > 0) setCompanyId(comps[0].id);
        if (seas.length > 0) setSeasonId(seas[0].id);
      } catch (err) {
        console.error("Failed to load metadata", err);
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, []);

  const handleBranchToggle = (branch: BranchName) => {
    if (selectedBranches.includes(branch)) {
      setSelectedBranches(selectedBranches.filter((b) => b !== branch));
    } else {
      setSelectedBranches([...selectedBranches, branch]);
    }
  };

  const handleSelectAllBranches = () => {
    if (selectedBranches.length === branchesList.length) {
      setSelectedBranches([]);
    } else {
      setSelectedBranches([...branchesList]);
    }
  };

  const handleSubmit = async (publishImmediately: boolean) => {
    try {
      setSubmitting(true);
      let targetCompanyId = companyId;

      if (isCreatingCompany) {
        if (!newCompanyName.trim()) {
          setToastMessage("Please provide a company name.");
          return;
        }
        const created = await coordinatorApi.createCompany({ name: newCompanyName.trim() });
        targetCompanyId = created.id;
      }

      const payload = {
        company_id: targetCompanyId,
        season_id: seasonId,
        title: title.trim(),
        description: description.trim(),
        min_cgpa: Number(minCgpa),
        max_backlogs: Number(maxBacklogs),
        package_lpa: Number(packageLpa),
        drive_date: driveDate,
        deadline: deadline,
        allowed_branches: selectedBranches,
        status: publishImmediately ? 'PUBLISHED' : 'DRAFT',
      };

      await jobApi.createJob(payload);
      setToastMessage(publishImmediately ? "Drive successfully published!" : "Drive saved as Draft.");
      
      // Reset form or refresh
      setTitle('');
      setDescription('');
    } catch (err: any) {
      setToastMessage(err.response?.data?.detail || "Failed to create drive.");
    } finally {
      setSubmitting(false);
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  const currentCompanyName = isCreatingCompany
    ? newCompanyName || 'New Company'
    : companies.find((c) => c.id === companyId)?.name || 'Select Company';

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-20 right-8 z-50 bg-slate-900 text-white px-5 py-3 rounded-xl shadow-xl flex items-center space-x-3 text-sm animate-in slide-in-from-top-4">
          <CheckCircle2 className="w-5 h-5 text-teal-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      <div>
        <h2 className="text-xl font-bold text-slate-800">Post a New Campus Placement Drive</h2>
        <p className="text-xs text-slate-500 mt-1">
          Configure drive details, academic criteria, and branch restrictions with a real-time student preview.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Form (7 Cols) */}
        <div className="lg:col-span-7 bg-white rounded-2xl p-6 sm:p-7 border border-slate-200 shadow-xs space-y-5">
          {/* Company Selection / Inline Creation */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold text-slate-700">Company</label>
              <button
                type="button"
                onClick={() => setIsCreatingCompany(!isCreatingCompany)}
                className="text-xs font-semibold text-teal-600 hover:text-teal-700"
              >
                {isCreatingCompany ? 'Choose Existing Company' : '+ Add New Company'}
              </button>
            </div>

            {isCreatingCompany ? (
              <input
                type="text"
                placeholder="Enter company name..."
                value={newCompanyName}
                onChange={(e) => setNewCompanyName(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
              />
            ) : (
              <select
                value={companyId}
                onChange={(e) => setCompanyId(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
              >
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Role Title & Season */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1.5">Job Role / Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
              />
            </div>
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1.5">Placement Season</label>
              <select
                value={seasonId}
                onChange={(e) => setSeasonId(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
              >
                {seasons.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.year})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Package, CGPA, Backlogs */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1.5">Package (LPA)</label>
              <input
                type="number"
                step="0.5"
                min="0"
                value={packageLpa}
                onChange={(e) => setPackageLpa(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
              />
            </div>
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1.5">Minimum CGPA</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="10"
                value={minCgpa}
                onChange={(e) => setMinCgpa(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
              />
            </div>
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1.5">Max Active Backlogs</label>
              <input
                type="number"
                min="0"
                value={maxBacklogs}
                onChange={(e) => setMaxBacklogs(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
              />
            </div>
          </div>

          {/* Dates */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1.5">Drive Date</label>
              <input
                type="date"
                value={driveDate}
                onChange={(e) => setDriveDate(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
              />
            </div>
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1.5">Application Deadline</label>
              <input
                type="date"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
              />
            </div>
          </div>

          {/* Branch Restrictions */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-slate-700">Eligible Branches</label>
              <button
                type="button"
                onClick={handleSelectAllBranches}
                className="text-xs text-slate-500 hover:text-slate-800 underline"
              >
                {selectedBranches.length === branchesList.length ? 'Clear All' : 'Select All'}
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {branchesList.map((branch) => {
                const isSelected = selectedBranches.includes(branch);
                return (
                  <button
                    key={branch}
                    type="button"
                    onClick={() => handleBranchToggle(branch)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all border ${
                      isSelected
                        ? 'bg-teal-600 text-white border-teal-600 shadow-2xs'
                        : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    {branch}
                  </button>
                );
              })}
            </div>
            <p className="text-[11px] text-slate-400 mt-1.5">
              {selectedBranches.length === 0
                ? 'Leaving all branches unselected opens this drive to all 5 accredited branches.'
                : `Students from ${selectedBranches.join(', ')} will be eligible.`}
            </p>
          </div>

          {/* Job Description */}
          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1.5">Job Description & Requirements</label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
            />
          </div>

          {/* Actions */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={() => handleSubmit(false)}
              disabled={submitting}
              className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl transition-colors flex items-center space-x-2"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save as Draft</span>
            </button>
            <button
              type="button"
              onClick={() => handleSubmit(true)}
              disabled={submitting}
              className="px-6 py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-xl transition-colors flex items-center space-x-2 shadow-xs"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{submitting ? 'Publishing...' : 'Publish Drive'}</span>
            </button>
          </div>
        </div>

        {/* Right Preview Card (5 Cols) */}
        <div className="lg:col-span-5 sticky top-24 space-y-3">
          <div className="flex items-center space-x-2 text-xs font-bold text-slate-500 uppercase tracking-wider">
            <Eye className="w-4 h-4 text-teal-600" />
            <span>Live Student-Facing Preview</span>
          </div>

          <div className="bg-white rounded-2xl p-6 border-2 border-teal-500/40 shadow-lg space-y-5">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center space-x-3.5">
                <div className="w-12 h-12 rounded-xl bg-slate-900 text-white font-extrabold flex items-center justify-center text-sm shadow-xs">
                  {currentCompanyName.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <h3 className="font-bold text-base text-slate-900">{title || 'Role Title'}</h3>
                  <p className="text-xs font-medium text-slate-500">{currentCompanyName}</p>
                </div>
              </div>

              <div className="text-right">
                <span className="text-base font-extrabold text-teal-700">{packageLpa} LPA</span>
                <p className="text-[11px] text-slate-400 font-medium">Annual CTC</p>
              </div>
            </div>

            <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
              {description || 'Job description preview...'}
            </p>

            <div className="grid grid-cols-3 gap-2 text-[11px] pt-2">
              <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
                <span className="text-slate-400 block">Min CGPA</span>
                <span className="font-bold text-slate-800">{minCgpa.toFixed(1)} / 10</span>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
                <span className="text-slate-400 block">Backlogs</span>
                <span className="font-bold text-slate-800">Max {maxBacklogs}</span>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
                <span className="text-slate-400 block">Drive Date</span>
                <span className="font-bold text-slate-800">{driveDate}</span>
              </div>
            </div>

            <div className="pt-2">
              <span className="text-[11px] text-slate-400 font-medium mr-1.5">Target Branches:</span>
              {selectedBranches.length === 0 ? (
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700">
                  Open to All
                </span>
              ) : (
                selectedBranches.map((b) => (
                  <span key={b} className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-teal-50 text-teal-700 border border-teal-200 mr-1">
                    {b}
                  </span>
                ))
              )}
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-50 text-teal-700 border border-teal-200">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-teal-600" />
                Eligible to Apply
              </span>
              <button 
                disabled 
                className="px-4 py-2 bg-teal-600 text-white rounded-xl text-xs font-bold opacity-80"
              >
                Apply Now
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
