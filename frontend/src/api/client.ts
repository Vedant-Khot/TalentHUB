import axios from 'axios';
import { 
  JobListing, Application, DashboardData, AnalyticsData,
  StudentProfile, Company, PlacementSeason, EligibilityCheckResult
} from '../types';

const API_BASE_URL = 'http://localhost:8001/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token from localStorage if available
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('talenthub_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Authentication
export const authApi = {
  login: async (email: string, password: string) => {
    const res = await apiClient.post('/auth/login', { email, password });
    return res.data;
  },
  getMe: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
};

// Students
export const studentApi = {
  getProfile: async (): Promise<StudentProfile> => {
    const res = await apiClient.get('/students/me');
    return res.data;
  },
  getDashboard: async (): Promise<DashboardData> => {
    const res = await apiClient.get('/students/dashboard');
    return res.data;
  },
  updateConsent: async (is_granted: boolean) => {
    const res = await apiClient.post('/students/me/consent', {
      policy_version: '1.0',
      purpose: 'PLACEMENT_DATA_PROCESSING',
      is_granted,
    });
    return res.data;
  },
};

// Jobs & Drives
export const jobApi = {
  listJobs: async (eligibleOnly = false): Promise<JobListing[]> => {
    const res = await apiClient.get('/jobs/', {
      params: { eligible_only: eligibleOnly },
    });
    return res.data;
  },
  getJob: async (jobId: number): Promise<JobListing> => {
    const res = await apiClient.get(`/jobs/${jobId}`);
    return res.data;
  },
  createJob: async (jobData: any): Promise<JobListing> => {
    const res = await apiClient.post('/jobs/', jobData);
    return res.data;
  },
  updateStatus: async (jobId: number, status: string): Promise<JobListing> => {
    const res = await apiClient.put(`/jobs/${jobId}/status`, null, {
      params: { new_status: status },
    });
    return res.data;
  },
};

// Applications
export const applicationApi = {
  apply: async (jobId: number): Promise<Application> => {
    const res = await apiClient.post('/applications/', { job_id: jobId });
    return res.data;
  },
  getMyApplications: async (): Promise<Application[]> => {
    const res = await apiClient.get('/applications/my');
    return res.data;
  },
  listAll: async (filters: { jobId?: number; stage?: string; branch?: string; search?: string } = {}): Promise<Application[]> => {
    const res = await apiClient.get('/applications/', {
      params: {
        job_id: filters.jobId,
        stage: filters.stage,
        branch: filters.branch,
        search: filters.search,
      },
    });
    return res.data;
  },
  shortlist: async (applicationId: number): Promise<Application> => {
    const res = await apiClient.post(`/applications/${applicationId}/shortlist`);
    return res.data;
  },
};

// Interviews
export const interviewApi = {
  scheduleRound: async (applicationId: number, data: { round_number: number; scheduled_time: string; venue_or_link: string; notes?: string }) => {
    const res = await apiClient.post(`/interviews/${applicationId}/schedule`, data);
    return res.data;
  },
  rescheduleRound: async (slotId: number, data: { scheduled_time: string; venue_or_link?: string; notes?: string }) => {
    const res = await apiClient.put(`/interviews/slots/${slotId}/reschedule`, data);
    return res.data;
  },
  recordResult: async (slotId: number, result: 'PASSED' | 'FAILED', markComplete = false, notes?: string) => {
    const res = await apiClient.put(`/interviews/slots/${slotId}/result`, { result, notes }, {
      params: { mark_all_rounds_complete: markComplete },
    });
    return res.data;
  },
};

// Offers
export const offerApi = {
  createOffer: async (applicationId: number, packageLpa: number, acceptanceDeadline?: string) => {
    const res = await apiClient.post(`/offers/${applicationId}/create`, {
      package_lpa: packageLpa,
      acceptance_deadline: acceptanceDeadline,
    });
    return res.data;
  },
  respond: async (offerId: number, action: 'ACCEPT' | 'DECLINE') => {
    const res = await apiClient.post(`/offers/${offerId}/respond`, { action });
    return res.data;
  },
  downloadLetterUrl: (offerId: number) => `${API_BASE_URL}/offers/${offerId}/letter`,
};

// Coordinator
export const coordinatorApi = {
  listCompanies: async (): Promise<Company[]> => {
    const res = await apiClient.get('/coordinator/companies');
    return res.data;
  },
  createCompany: async (companyData: { name: string; website?: string; contact_email?: string; description?: string }): Promise<Company> => {
    const res = await apiClient.post('/coordinator/companies', companyData);
    return res.data;
  },
  listSeasons: async (): Promise<PlacementSeason[]> => {
    const res = await apiClient.get('/coordinator/seasons');
    return res.data;
  },
  getAnalytics: async (): Promise<AnalyticsData> => {
    const res = await apiClient.get('/coordinator/analytics');
    return res.data;
  },
};
