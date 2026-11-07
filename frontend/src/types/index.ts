export type UserRole = 'STUDENT' | 'COMPANY_REPRESENTATIVE' | 'PLACEMENT_COORDINATOR';

export type BranchName = 'CSE' | 'ECE' | 'ISE' | 'MECH' | 'CIVIL';

export type JobStatus = 'DRAFT' | 'PUBLISHED' | 'CLOSED' | 'CANCELLED';

export type ApplicationStage = 
  | 'APPLIED' 
  | 'SHORTLISTED' 
  | 'INTERVIEW_SCHEDULED' 
  | 'INTERVIEWED' 
  | 'OFFERED' 
  | 'ACCEPTED';

export type InterviewStatus = 'SCHEDULED' | 'COMPLETED' | 'CANCELLED' | 'RESCHEDULED';

export type InterviewResult = 'PENDING' | 'PASSED' | 'FAILED';

export type OfferStatus = 'PENDING' | 'ACCEPTED' | 'DECLINED';

export interface User {
  id: number;
  email: string;
  role: UserRole;
  is_active: boolean;
  student_id?: number | null;
  company_id?: number | null;
}

export interface StudentProfile {
  id: number;
  user_id: number;
  usn: string;
  full_name: string;
  email: string;
  branch: BranchName;
  cgpa: number;
  active_backlogs: number;
  cleared_backlogs: number;
  phone?: string | null;
  has_active_consent: boolean;
  accepted_offer_this_season: boolean;
}

export interface EligibilityCheckResult {
  is_eligible: boolean;
  cgpa_pass: boolean;
  backlogs_pass: boolean;
  season_offer_pass: boolean;
  branch_pass: boolean;
  rejection_reasons: string[];
  inputs_evaluated: Record<string, any>;
}

export interface JobListing {
  id: number;
  company_id: number;
  company_name: string;
  season_id: number;
  season_name: string;
  title: string;
  description: string;
  min_cgpa: number;
  max_backlogs: number;
  package_lpa: number;
  drive_date: string;
  deadline: string;
  status: JobStatus;
  allowed_branches: string[];
  is_open_to_all_branches: boolean;
  eligibility?: EligibilityCheckResult | null;
  has_applied: boolean;
  application_stage?: ApplicationStage | null;
}

export interface InterviewSlot {
  id: number;
  application_id: number;
  round_number: number;
  scheduled_time: string;
  venue_or_link: string;
  status: InterviewStatus;
  result: InterviewResult;
  notes?: string | null;
}

export interface Offer {
  id: number;
  application_id: number;
  package_lpa: number;
  issue_date: string;
  acceptance_deadline?: string | null;
  letter_storage_key: string;
  status: OfferStatus;
  response_timestamp?: string | null;
}

export interface ApplicationStatusHistory {
  id: number;
  from_stage: string;
  to_stage: string;
  changed_by_user_id?: number | null;
  reason?: string | null;
  changed_at: string;
}

export interface Application {
  id: number;
  student_id: number;
  student_name: string;
  student_usn: string;
  student_branch: string;
  student_cgpa: number;
  job_id: number;
  job_title: string;
  company_name: string;
  package_lpa: number;
  stage: ApplicationStage;
  applied_at: string;
  interviews: InterviewSlot[];
  offer?: Offer | null;
  history: ApplicationStatusHistory[];
}

export interface Company {
  id: number;
  name: string;
  website?: string | null;
  contact_email?: string | null;
  description?: string | null;
}

export interface PlacementSeason {
  id: number;
  year: number;
  name: string;
  is_active: boolean;
  start_date: string;
  end_date: string;
}

export interface DashboardData {
  student: {
    id: number;
    full_name: string;
    usn: string;
    branch: string;
    cgpa: number;
    active_backlogs: number;
    accepted_offer_this_season: boolean;
  };
  active_season: {
    id: number;
    name: string;
    year: number;
  } | null;
  stage_counts: Record<string, number>;
  upcoming_interview: {
    slot_id: number;
    company_name: string;
    job_title: string;
    round_number: number;
    scheduled_time: string;
    venue_or_link: string;
    notes?: string | null;
  } | null;
  eligible_drives: Array<{
    id: number;
    title: string;
    company_name: string;
    package_lpa: number;
    drive_date: string;
    deadline: string;
    min_cgpa: number;
    has_applied: boolean;
  }>;
}

export interface AnalyticsData {
  total_students: number;
  total_drives: number;
  placed_students: number;
  placement_percentage: number;
  average_package_lpa: number;
  highest_package_lpa: number;
  stage_breakdown: Record<string, number>;
  branch_placement: Record<string, number>;
}
