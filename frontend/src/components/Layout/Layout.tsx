import React, { useMemo, useState } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Bot,
  Building2,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
  Palette,
  Plug,
  X
} from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

const Layout: React.FC = () => {
  const { t, i18n } = useTranslation()
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const [mobileOpen, setMobileOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  const navigation = useMemo(
    () => [
      { label: i18n.language === 'ar' ? 'نظرة عامة' : 'Overview', href: '/dashboard', icon: LayoutDashboard },
      { label: t('navigation.agents'), href: '/dashboard/agents', icon: Bot },
      { label: i18n.language === 'ar' ? 'استوديو الوكلاء' : 'Agent Studio', href: '/dashboard/agent-studio', icon: Palette },
      { label: t('navigation.conversations'), href: '/dashboard/conversations', icon: MessageSquare },
      { label: t('navigation.integrations'), href: '/dashboard/integrations', icon: Plug },
      { label: i18n.language === 'ar' ? 'المؤسسة' : 'Organization', href: '/dashboard/organization', icon: Building2 }
    ],
    [i18n.language, t]
  )

  const isActive = (href: string) => {
    if (href === '/dashboard') return location.pathname === '/dashboard'
    return location.pathname.startsWith(href)
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="relative min-h-screen bg-app-bg text-slate-900">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.2),_transparent_55%)]" />

      {mobileOpen && (
        <button
          aria-label="Close menu"
          className="fixed inset-0 z-30 bg-slate-950/35 backdrop-blur-[1px] lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 z-40 flex flex-col border-slate-200/70 bg-white/80 backdrop-blur-xl transition-all duration-300 lg:border-e ${
          mobileOpen ? 'left-0' : '-left-full'
        } ${collapsed ? 'lg:w-20' : 'lg:w-72'} w-72 lg:left-0`}
      >
        <div className="flex h-16 items-center justify-between border-b border-slate-200/70 px-4">
          <Link to="/dashboard" className="flex items-center gap-3">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-sky-400 text-sm font-bold text-white shadow-lg shadow-blue-500/25">
              J
            </span>
            {!collapsed && <span className="text-base font-semibold tracking-tight">Joulaa AI</span>}
          </Link>
          <button
            onClick={() => setMobileOpen(false)}
            className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 lg:hidden"
            aria-label="Close sidebar"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {navigation.map((item) => {
            const Icon = item.icon
            const active = isActive(item.href)

            return (
              <Link
                key={item.href}
                to={item.href}
                onClick={() => setMobileOpen(false)}
                className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                  active
                    ? 'bg-gradient-to-r from-blue-600 to-sky-500 text-white shadow-lg shadow-blue-500/25'
                    : 'text-slate-700 hover:bg-blue-50 hover:text-blue-700'
                } ${collapsed ? 'justify-center' : ''}`}
              >
                <Icon size={18} />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </Link>
            )
          })}
        </nav>

        <div className="border-t border-slate-200/70 p-3">
          <div className={`mb-2 rounded-xl bg-slate-50 p-3 ${collapsed ? 'text-center' : ''}`}>
            {!collapsed && (
              <>
                <p className="truncate text-sm font-semibold text-slate-800">{user?.full_name_ar || user?.full_name_en || user?.username}</p>
                <p className="truncate text-xs text-slate-500">{user?.email}</p>
              </>
            )}
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:-translate-y-0.5 hover:shadow-md"
          >
            <LogOut size={16} />
            {!collapsed && <span>{t('auth.logout')}</span>}
          </button>
        </div>
      </aside>

      <div className={`relative min-h-screen transition-all duration-300 ${collapsed ? 'lg:ps-20' : 'lg:ps-72'}`}>
        <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/70 backdrop-blur-xl">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setMobileOpen(true)}
                className="rounded-lg p-2 text-slate-600 transition hover:bg-slate-100 lg:hidden"
                aria-label="Open sidebar"
              >
                <Menu size={18} />
              </button>
              <button
                onClick={() => setCollapsed((prev) => !prev)}
                className="hidden rounded-lg p-2 text-slate-600 transition hover:bg-slate-100 lg:inline-flex"
                aria-label="Toggle sidebar width"
              >
                {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
              </button>
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">AI Operations</p>
                <p className="text-sm font-semibold text-slate-800">{t('navigation.dashboard')}</p>
              </div>
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1600px] p-4 sm:p-6 lg:p-8">
          <div className="animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}

export default Layout
