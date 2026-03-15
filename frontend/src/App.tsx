import React, { Suspense, lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import './i18n'

import ProtectedRoute from './components/Auth/ProtectedRoute'

const HomePage = lazy(() => import('./pages/HomePage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const AgentsPage = lazy(() => import('./pages/AgentsPage'))
const ConversationsPage = lazy(() => import('./pages/ConversationsPage'))
const ChatPage = lazy(() => import('./pages/ChatPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))
const IntegrationsPage = lazy(() => import('./pages/IntegrationsPage'))
const OrganizationSettings = lazy(() => import('./pages/OrganizationSettings'))
const AgentStudioPage = lazy(() => import('./pages/AgentStudioPage'))
const DashboardOverview = lazy(() => import('./components/Dashboard/DashboardOverview'))
const Layout = lazy(() => import('./components/Layout/Layout'))

const RouteLoading: React.FC = () => (
  <div className="flex min-h-screen items-center justify-center bg-app-bg px-4">
    <div className="card w-full max-w-md text-center">
      <div className="skeleton mx-auto h-10 w-40" />
      <div className="skeleton mx-auto mt-4 h-4 w-56" />
    </div>
  </div>
)

function App() {
  const { i18n } = useTranslation()

  React.useEffect(() => {
    const dir = i18n.language === 'ar' ? 'rtl' : 'ltr'
    document.documentElement.dir = dir
    document.documentElement.lang = i18n.language
  }, [i18n.language])

  return (
    <div className="min-h-screen font-arabic">
      <Suspense fallback={<RouteLoading />}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardOverview />} />
            <Route path="agents" element={<AgentsPage />} />
            <Route path="agent-studio" element={<AgentStudioPage />} />
            <Route path="conversations" element={<ConversationsPage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="chat/:conversationId" element={<ChatPage />} />
            <Route path="integrations" element={<IntegrationsPage />} />
            <Route path="organization" element={<OrganizationSettings />} />
            <Route path="settings" element={<OrganizationSettings />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>

          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </div>
  )
}

export default App
