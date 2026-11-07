import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, StudentProfile } from '../types';
import { authApi, studentApi } from '../api/client';

interface AuthContextType {
  token: string | null;
  user: User | null;
  student: StudentProfile | null;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => void;
  switchDemoUser: (type: 'student1' | 'student2' | 'student3' | 'coordinator') => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('talenthub_token'));
  const [user, setUser] = useState<User | null>(null);
  const [student, setStudent] = useState<StudentProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchCurrentUser = async () => {
    try {
      if (!token) {
        setUser(null);
        setStudent(null);
        setIsLoading(false);
        return;
      }
      const userData = await authApi.getMe();
      setUser(userData);
      if (userData.role === 'STUDENT') {
        const studentData = await studentApi.getProfile();
        setStudent(studentData);
      } else {
        setStudent(null);
      }
    } catch (err) {
      console.error("Failed to load user profile", err);
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, [token]);

  const login = async (email: string, pass: string) => {
    setIsLoading(true);
    const data = await authApi.login(email, pass);
    localStorage.setItem('talenthub_token', data.access_token);
    setToken(data.access_token);
  };

  const logout = () => {
    localStorage.removeItem('talenthub_token');
    setToken(null);
    setUser(null);
    setStudent(null);
  };

  const switchDemoUser = async (type: 'student1' | 'student2' | 'student3' | 'coordinator') => {
    if (type === 'student1') {
      await login('student1@college.edu', 'StudentPass123!');
    } else if (type === 'student2') {
      await login('student2@college.edu', 'StudentPass123!');
    } else if (type === 'student3') {
      await login('student3@college.edu', 'StudentPass123!');
    } else {
      await login('coordinator@college.edu', 'CoordinatorPass123!');
    }
  };

  const refreshProfile = async () => {
    await fetchCurrentUser();
  };

  return (
    <AuthContext.Provider value={{ token, user, student, isLoading, login, logout, switchDemoUser, refreshProfile }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
