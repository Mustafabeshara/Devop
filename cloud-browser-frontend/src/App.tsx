
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { Layout } from './components/layout/Layout'
import { LoginPage } from './pages/auth/LoginPage'
import { RegisterPage } from './pages/auth/RegisterPage'
import { DashboardPage } from './pages/dashboard/DashboardPage'
import { SessionsPage } from './pages/sessions/SessionsPage'
import { SessionDetailPage } from './pages/sessions/SessionDetailPage'
import { BrowserPage } from './pages/browser/BrowserPage'
import { CodeAnalysisPage } from './pages/code/CodeAnalysisPage'
import { ProfilePage } from './pages/profile/ProfilePage'
import { AdminPage } from './pages/admin/AdminPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { useAuth } from './hooks/useAuth'

function AppContent() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="loading-spinner w-8 h-8 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Cloud Browser Service...</p>
        </div>
      </div>
    )
  }

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={
        user ? <Navigate to="/dashboard" replace /> : <LoginPage />
      } />
      <Route path="/register" element={
        user ? <Navigate to="/dashboard" replace /> : <RegisterPage />
      } />
      
      {/* Protected routes */}
      <Route path="/" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        {/* Redirect root to dashboard */}
        <Route index element={<Navigate to="/dashboard" replace />} />
        
        {/* Main application routes */}
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="sessions" element={<SessionsPage />} />
        <Route path="sessions/:sessionId" element={<SessionDetailPage />} />
        <Route path="browser/:sessionId" element={<BrowserPage />} />
        <Route path="code" element={<CodeAnalysisPage />} />
        <Route path="profile" element={<ProfilePage />} />
        
        {/* Admin routes */}
        <Route path="admin/*" element={
          <ProtectedRoute requireAdmin>
            <AdminPage />
          </ProtectedRoute>
        } />
      </Route>
      
      {/* 404 page */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
