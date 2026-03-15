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

const LoginPage: React.FC = () => {
  const { t, i18n } = useTranslation()
  const { login, isLoading } = useAuth()
  const navigate = useNavigate()

  const [formData, setFormData] = useState({
    email_or_username: '',
    password: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState<{ [key: string]: string }>({})

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: '' }))
  }

  const validateForm = () => {
    const newErrors: { [key: string]: string } = {}

    if (!formData.email_or_username.trim()) {
      newErrors.email_or_username = t('auth.emailRequired')
    }

    if (!formData.password) {
      newErrors.password = t('auth.passwordRequired')
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    try {
      await login(formData)
      navigate('/dashboard')
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      toast.error(detail || t('auth.loginFailed'))
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-app-bg px-4 py-10">
      <LocaleSwitcher />

      <Card glass className="w-full max-w-md animate-lift border-blue-100">
        <h1 className="mb-1 text-2xl font-bold text-slate-900">{t('auth.login')}</h1>
        <p className="mb-6 text-sm text-slate-600">
          {i18n.language === 'ar'
            ? 'ادخل إلى منصة جولة لإدارة الوكلاء والمحادثات.'
            : 'Access Joulaa to manage agents and conversations.'}
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <FloatingField
            type="text"
            name="email_or_username"
            label={t('auth.emailOrUsername')}
            value={formData.email_or_username}
            onChange={handleChange}
            disabled={isLoading}
            error={errors.email_or_username}
          />

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

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? t('auth.loggingIn') : t('auth.login')}
          </Button>
        </form>

        <p className="mt-5 text-center text-sm text-slate-600">
          {t('auth.noAccount')}{' '}
          <Link to="/register" className="font-semibold text-blue-600 hover:text-blue-700">
            {t('auth.register')}
          </Link>
        </p>
      </Card>
    </div>
  )
}

export default LoginPage
