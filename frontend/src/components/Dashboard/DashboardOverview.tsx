import React from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import {
  Activity,
  BarChart3,
  Bot,
  CheckCircle,
  Clock,
  MessageSquare,
  Plus,
  TrendingUp,
  Users,
  AlertTriangle
} from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import Card from '../ui/Card'
import PageHeader from '../ui/PageHeader'
import Button from '../ui/Button'

const DashboardOverview: React.FC = () => {
  const { t, i18n } = useTranslation()
  const { user } = useAuth()

  const stats = [
    { name: i18n.language === 'ar' ? 'إجمالي الوكلاء' : 'Total Agents', value: '12', change: '+2', icon: Bot, href: '/dashboard/agents' },
    { name: i18n.language === 'ar' ? 'المحادثات النشطة' : 'Active Conversations', value: '48', change: '+12%', icon: MessageSquare, href: '/dashboard/conversations' },
    { name: i18n.language === 'ar' ? 'المستخدمون' : 'Users', value: '156', change: '+8', icon: Users, href: '/dashboard/organization' },
    { name: i18n.language === 'ar' ? 'معدل النجاح' : 'Success Rate', value: '94%', change: '+2%', icon: BarChart3, href: '/dashboard/integrations' }
  ]

  const recentActivities = [
    {
      id: 1,
      message: i18n.language === 'ar' ? 'تم إنشاء وكيل جديد لخدمة العملاء.' : 'A new customer support agent was created.',
      time: i18n.language === 'ar' ? 'منذ ساعتين' : '2 hours ago',
      icon: CheckCircle,
      status: 'success'
    },
    {
      id: 2,
      message: i18n.language === 'ar' ? 'تمت مزامنة تكاملات المؤسسة بنجاح.' : 'Organization integrations synced successfully.',
      time: i18n.language === 'ar' ? 'منذ 4 ساعات' : '4 hours ago',
      icon: Activity,
      status: 'neutral'
    },
    {
      id: 3,
      message: i18n.language === 'ar' ? 'هناك بطء في أحد مصادر البيانات الخارجية.' : 'One external data source is responding slowly.',
      time: i18n.language === 'ar' ? 'منذ 6 ساعات' : '6 hours ago',
      icon: AlertTriangle,
      status: 'warning'
    }
  ]

  return (
    <div>
      <PageHeader
        title={t('dashboard.welcome')}
        subtitle={
          user
            ? `${i18n.language === 'ar' ? 'مرحباً' : 'Welcome'}, ${user.full_name_ar || user.full_name_en || user.username}`
            : i18n.language === 'ar'
              ? 'لوحة تشغيل موحدة لمراقبة وكلائك الذكيين.'
              : 'A unified control center for your AI operations.'
        }
        action={
          <Link to="/dashboard/agent-studio">
            <Button className="gap-2">
              <Plus size={16} />
              {i18n.language === 'ar' ? 'وكيل جديد' : 'New Agent'}
            </Button>
          </Link>
        }
      />

      <section className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Link key={stat.name} to={stat.href}>
              <Card className="card-hover h-full">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm text-slate-600">{stat.name}</p>
                    <p className="mt-2 text-3xl font-bold text-slate-900">{stat.value}</p>
                    <p className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-emerald-600">
                      <TrendingUp size={14} />
                      {stat.change}
                    </p>
                  </div>
                  <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                    <Icon size={20} />
                  </span>
                </div>
              </Card>
            </Link>
          )
        })}
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <h2 className="mb-4 text-lg font-semibold text-slate-900">{t('dashboard.quickActions')}</h2>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <Link to="/dashboard/agent-studio" className="rounded-xl border border-slate-200 p-4 transition hover:-translate-y-1 hover:bg-blue-50/60">
              <h3 className="font-semibold text-slate-900">{i18n.language === 'ar' ? 'إنشاء وكيل' : 'Create Agent'}</h3>
              <p className="mt-1 text-sm text-slate-600">{i18n.language === 'ar' ? 'ابدأ وكيل جديد عبر الاستوديو.' : 'Launch a new assistant from studio.'}</p>
            </Link>
            <Link to="/dashboard/chat" className="rounded-xl border border-slate-200 p-4 transition hover:-translate-y-1 hover:bg-blue-50/60">
              <h3 className="font-semibold text-slate-900">{i18n.language === 'ar' ? 'محادثة مباشرة' : 'Live Chat'}</h3>
              <p className="mt-1 text-sm text-slate-600">{i18n.language === 'ar' ? 'اختبر الوكلاء في واجهة الدردشة.' : 'Test your agents in chat mode.'}</p>
            </Link>
          </div>
        </Card>

        <Card>
          <h2 className="mb-4 text-lg font-semibold text-slate-900">{t('dashboard.recentActivity')}</h2>
          <div className="space-y-3">
            {recentActivities.map((activity) => {
              const Icon = activity.icon
              return (
                <div key={activity.id} className="flex items-start gap-3 rounded-xl border border-slate-200/70 p-3">
                  <span
                    className={`mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded-lg ${
                      activity.status === 'success'
                        ? 'bg-emerald-50 text-emerald-600'
                        : activity.status === 'warning'
                          ? 'bg-amber-50 text-amber-600'
                          : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    <Icon size={16} />
                  </span>
                  <div>
                    <p className="text-sm font-medium text-slate-800">{activity.message}</p>
                    <p className="mt-1 inline-flex items-center gap-1 text-xs text-slate-500">
                      <Clock size={12} />
                      {activity.time}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </Card>
      </section>
    </div>
  )
}

export default DashboardOverview
