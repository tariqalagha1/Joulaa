import React from 'react'
import { useTranslation } from 'react-i18next'

const LocaleSwitcher: React.FC = () => {
  const { i18n } = useTranslation()

  const toggleLanguage = () => {
    const nextLang = i18n.language === 'ar' ? 'en' : 'ar'
    i18n.changeLanguage(nextLang)
  }

  const label = i18n.language === 'ar' ? 'EN' : 'AR'

  return (
    <button
      onClick={toggleLanguage}
      className="absolute top-4 left-4 rounded-full border border-primary-500 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-wide text-primary-600 shadow-sm transition hover:bg-primary-50"
      aria-label="Switch language"
    >
      {label}
    </button>
  )
}

export default LocaleSwitcher
