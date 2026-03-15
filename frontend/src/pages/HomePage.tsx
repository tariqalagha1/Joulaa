import React from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { ArrowRight, Bot, Gauge, ShieldCheck } from 'lucide-react'
import LocaleSwitcher from '../components/LocaleSwitcher/LocaleSwitcher'

const HomePage: React.FC = () => {
  const { t, i18n } = useTranslation()

  const features = [
    {
      icon: Bot,
      title: i18n.language === 'ar' ? 'وكلاء ذكيون جاهزون' : 'Production AI agents',
      text: i18n.language === 'ar' ? 'إطلاق وكلاء متخصصين بسرعة مع إدارة مركزية.' : 'Launch specialized agents quickly with centralized control.'
    },
    {
      icon: Gauge,
      title: i18n.language === 'ar' ? 'لوحات تشغيل واضحة' : 'Clear operations dashboards',
      text: i18n.language === 'ar' ? 'مراقبة الأداء والمحادثات من واجهة واحدة.' : 'Track performance and conversations from one workspace.'
    },
    {
      icon: ShieldCheck,
      title: i18n.language === 'ar' ? 'أساس قوي للمؤسسات' : 'Enterprise-ready foundation',
      text: i18n.language === 'ar' ? 'تصميم آمن ومنظم يدعم التوسع.' : 'Structured and secure design that scales with your business.'
    }
  ]

  return (
    <div className="relative min-h-screen bg-app-bg px-4 py-10 sm:px-6 lg:px-8">
      <LocaleSwitcher />

      <div className="mx-auto max-w-6xl">
        <div className="card mb-8 overflow-hidden border-blue-100 bg-white/80 backdrop-blur-xl sm:p-10">
          <div className="grid gap-8 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="mb-3 inline-flex rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-blue-700">
                AI SaaS Platform
              </p>
              <h1 className="text-3xl font-extrabold leading-tight text-slate-900 sm:text-5xl">{t('dashboard.welcome')}</h1>
              <p className="mt-4 text-base leading-7 text-slate-600 sm:text-lg">
                {i18n.language === 'ar'
                  ? 'منصة جولة لإدارة الوكلاء الذكيين والمحادثات والتكاملات ضمن تجربة تشغيل حديثة.'
                  : 'Joulaa helps teams run AI agents, conversations, and integrations in one modern operating layer.'}
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link to="/login" className="btn-primary gap-2">
                  {t('auth.login')}
                  <ArrowRight size={16} />
                </Link>
                <Link to="/register" className="btn-outline">
                  {t('auth.register')}
                </Link>
              </div>
            </div>

            <div className="grid gap-4">
              {features.map((feature) => {
                const Icon = feature.icon
                return (
                  <div key={feature.title} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft transition hover:-translate-y-1 hover:shadow-medium">
                    <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                      <Icon size={18} />
                    </div>
                    <h2 className="text-lg font-bold text-slate-900">{feature.title}</h2>
                    <p className="mt-1 text-sm text-slate-600">{feature.text}</p>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage
