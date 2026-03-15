import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../contexts/AuthContext'
import LocaleSwitcher from '../components/LocaleSwitcher/LocaleSwitcher'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import FloatingField from '../components/ui/FloatingField'

const RegisterPage: React.FC = () => {
  const { t, i18n } = useTranslation()
  const { register, isLoading } = useAuth()
  const navigate = useNavigate()

  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    full_name_ar: '',
    full_name_en: '',
    language_preference: 'ar'
  })
  const [errors, setErrors] = useState<{ [key: string]: string }>({})
  const [showPassword, setShowPassword] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: '' }))
  }

  const validateForm = () => {
    const newErrors: { [key: string]: string } = {}

    if (!formData.email.trim()) {
      newErrors.email = t('auth.emailRequired')
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = t('auth.emailInvalid')
    }

    if (!formData.username.trim()) {
      newErrors.username = t('auth.usernameRequired')
    } else if (formData.username.length < 3) {
      newErrors.username = t('auth.usernameMinLength')
    }

    if (!formData.password) {
      newErrors.password = t('auth.passwordRequired')
    } else if (formData.password.length < 8) {
      newErrors.password = t('auth.passwordMinLength')
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = t('auth.passwordMismatch')
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    try {
      const { confirmPassword, ...registerData } = formData
      await register(registerData)
      navigate('/dashboard')
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      toast.error(detail || t('auth.registrationFailed'))
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-app-bg px-4 py-10">
      <LocaleSwitcher />

      <Card glass className="w-full max-w-xl animate-lift border-blue-100">
        <div className="mb-6 flex items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">{t('auth.register')}</h1>
            <p className="mt-1 text-sm text-slate-600">
              {i18n.language === 'ar'
                ? 'أنشئ حسابك وابدأ تشغيل وكلائك الذكيين.'
                : 'Create your account and start running AI agents.'}
            </p>
          </div>
          <button
            type="button"
            onClick={() => i18n.changeLanguage(i18n.language === 'ar' ? 'en' : 'ar')}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            {i18n.language === 'ar' ? 'English' : 'العربية'}
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <FloatingField
            type="email"
            name="email"
            label={t('auth.email')}
            value={formData.email}
            onChange={handleChange}
            disabled={isLoading}
            error={errors.email}
          />

          <FloatingField
            type="text"
            name="username"
            label={t('auth.username')}
            value={formData.username}
            onChange={handleChange}
            disabled={isLoading}
            error={errors.username}
          />

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FloatingField
              type="text"
              name="full_name_ar"
              label={t('auth.fullNameAr')}
              value={formData.full_name_ar}
              onChange={handleChange}
              disabled={isLoading}
            />
            <FloatingField
              type="text"
              name="full_name_en"
              label={t('auth.fullNameEn')}
              value={formData.full_name_en}
              onChange={handleChange}
              disabled={isLoading}
            />
          </div>

          <div className="relative">
            <FloatingField
              type={showPassword ? 'text' : 'password'}
              name="password"
              label={t('auth.password')}
              value={formData.password}
              onChange={handleChange}
              disabled={isLoading}
              error={errors.password}
              className="pe-10"
            />
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              className="absolute end-3 top-3 rounded-md p-1 text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
              aria-label="Toggle password visibility"
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>

          <FloatingField
            type={showPassword ? 'text' : 'password'}
            name="confirmPassword"
            label={t('auth.confirmPassword')}
            value={formData.confirmPassword}
            onChange={handleChange}
            disabled={isLoading}
            error={errors.confirmPassword}
          />

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-slate-700">{t('auth.language')}</span>
            <select
              name="language_preference"
              value={formData.language_preference}
              onChange={handleChange}
              className="input-field"
              disabled={isLoading}
            >
              <option value="ar">العربية</option>
              <option value="en">English</option>
            </select>
          </label>

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? t('auth.registering') : t('auth.createAccount')}
          </Button>
        </form>

        <p className="mt-5 text-center text-sm text-slate-600">
          {t('auth.haveAccount')}{' '}
          <Link to="/login" className="font-semibold text-blue-600 hover:text-blue-700">
            {t('auth.login')}
          </Link>
        </p>
      </Card>
    </div>
  )
}

export default RegisterPage
