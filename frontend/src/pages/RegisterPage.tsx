import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import toast from 'react-hot-toast'
import LocaleSwitcher from '../components/LocaleSwitcher/LocaleSwitcher'

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
    setFormData(prev => ({ ...prev, [name]: value }))
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
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
    
    if (!validateForm()) {
      return
    }

    try {
      const { confirmPassword, ...registerData } = formData
      await register(registerData)
      navigate('/dashboard')
    } catch (error: any) {
      console.error('Registration failed:', error)
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail)
      } else {
        toast.error(t('auth.registrationFailed'))
      }
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-secondary-50 py-8 relative">
      <LocaleSwitcher />
      <div className="card w-full max-w-md">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">
            {t('auth.register')}
          </h2>
          <button
            type="button"
            onClick={() => i18n.changeLanguage(i18n.language === 'ar' ? 'en' : 'ar')}
            className="text-xs font-semibold text-primary-600 hover:text-primary-500"
          >
            {i18n.language === 'ar' ? 'English' : 'العربية'}
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              {t('auth.email')}
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className={`input-field ${errors.email ? 'border-red-500' : ''}`}
              placeholder={t('auth.emailPlaceholder')}
              disabled={isLoading}
            />
            {errors.email && (
              <p className="text-red-500 text-sm mt-1">{errors.email}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">
              {t('auth.username')}
            </label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              className={`input-field ${errors.username ? 'border-red-500' : ''}`}
              placeholder={t('auth.username')}
              disabled={isLoading}
            />
            {errors.username && (
              <p className="text-red-500 text-sm mt-1">{errors.username}</p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                {t('auth.fullNameAr')}
              </label>
              <input
                type="text"
                name="full_name_ar"
                value={formData.full_name_ar}
                onChange={handleChange}
                className="input-field"
                placeholder="الاسم الكامل"
                disabled={isLoading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                {t('auth.fullNameEn')}
              </label>
              <input
                type="text"
                name="full_name_en"
                value={formData.full_name_en}
                onChange={handleChange}
                className="input-field"
                placeholder="Full Name"
                disabled={isLoading}
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">
              {t('auth.password')}
            </label>
            <input
              type={showPassword ? 'text' : 'password'}
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={`input-field ${errors.password ? 'border-red-500' : ''}`}
              placeholder={t('auth.passwordPlaceholder')}
              disabled={isLoading}
            />
            {errors.password && (
              <p className="text-red-500 text-sm mt-1">{errors.password}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">
              {t('auth.confirmPassword')}
            </label>
            <input
              type={showPassword ? 'text' : 'password'}
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              className={`input-field ${errors.confirmPassword ? 'border-red-500' : ''}`}
              placeholder={t('auth.passwordPlaceholder')}
              disabled={isLoading}
            />
            <div className="flex items-center text-xs text-gray-500 mt-1 space-x-2">
              <input
                id="register-show-password"
                type="checkbox"
                checked={showPassword}
                onChange={() => setShowPassword(prev => !prev)}
                className="h-4 w-4 rounded border-gray-300 focus:ring-primary-500 text-primary-600"
              />
              <label htmlFor="register-show-password">{t('auth.showPassword')}</label>
            </div>
            {errors.confirmPassword && (
              <p className="text-red-500 text-sm mt-1">{errors.confirmPassword}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">
              {t('auth.language')}
            </label>
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
          </div>
          <button 
            type="submit" 
            className="btn-primary w-full"
            disabled={isLoading}
          >
            {isLoading ? t('auth.registering') : t('auth.register')}
          </button>
        </form>
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            {t('auth.haveAccount')}{' '}
            <Link to="/login" className="text-primary-600 hover:text-primary-700 font-medium">
              {t('auth.login')}
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default RegisterPage
