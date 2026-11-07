import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { StudentDashboard } from './pages/StudentDashboard';
import { JobDrives } from './pages/JobDrives';
import { MyApplications } from './pages/MyApplications';
import { PostDrive } from './pages/PostDrive';
import { ApplicantsAndOffers } from './pages/ApplicantsAndOffers';
import { CoordinatorDashboard } from './pages/CoordinatorDashboard';

const MainLayout: React.FC = () => {
  const { user, token, switchDemoUser, isLoading } = useAuth();
  const [currentTab, setCurrentTab] = useState<string>('dashboard');

  // Auto-seed initial login as Student 1 if not logged in
  useEffect(() => {
    if (!token && !isLoading) {
      switchDemoUser('student1');
    }
  }, [token, isLoading]);

  // Adjust default tab when role changes
  useEffect(() => {
    if (user?.role === 'PLACEMENT_COORDINATOR') {
      if (['dashboard', 'drives', 'applications'].includes(currentTab)) {
        setCurrentTab('coordinator-dashboard');
      }
    } else if (user?.role === 'STUDENT') {
      if (['coordinator-dashboard', 'post-drive', 'applicants'].includes(currentTab)) {
        setCurrentTab('dashboard');
      }
    }
  }, [user?.role]);

  const getPageTitle = () => {
    switch (currentTab) {
      case 'dashboard': return 'Student Placement Dashboard';
      case 'drives': return 'Campus Job Drives';
      case 'applications': return 'My Applications Tracker';
      case 'coordinator-dashboard': return 'Placement Overview & Analytics';
      case 'post-drive': return 'Post a Campus Drive';
      case 'applicants': return 'Applicants & Offers Management';
      default: return 'TalentHub Portal';
    }
  };

  const renderContent = () => {
    switch (currentTab) {
      case 'dashboard':
        return <StudentDashboard onNavigateTab={setCurrentTab} />;
      case 'drives':
        return <JobDrives />;
      case 'applications':
        return <MyApplications />;
      case 'coordinator-dashboard':
        return <CoordinatorDashboard />;
      case 'post-drive':
        return <PostDrive />;
      case 'applicants':
        return <ApplicantsAndOffers />;
      default:
        return <StudentDashboard onNavigateTab={setCurrentTab} />;
    }
  };

  return (
    <div className="flex min-h-screen bg-[#F8FAFC]">
      <Sidebar currentTab={currentTab} setCurrentTab={setCurrentTab} />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar 
          title={getPageTitle()} 
          subtitle="TalentHub Campus Placement Platform"
        />
        <main className="flex-1">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export function App() {
  return (
    <AuthProvider>
      <MainLayout />
    </AuthProvider>
  );
}

export default App;
