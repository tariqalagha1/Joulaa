import React from 'react'
import { cn } from '../../lib/cn'

interface FloatingFieldProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'placeholder'> {
  label: string
  error?: string
}

const FloatingField: React.FC<FloatingFieldProps> = ({ label, error, className, id, ...props }) => {
  const inputId = id || props.name

  return (
    <label className="group relative block">
      <input
        id={inputId}
        placeholder=" "
        className={cn(
          'peer h-12 w-full rounded-xl border bg-white px-3 text-sm text-slate-900 transition placeholder:text-transparent focus:outline-none focus:ring-2',
          error
            ? 'border-red-300 focus:border-red-400 focus:ring-red-400/40'
            : 'border-slate-300 focus:border-blue-400 focus:ring-blue-400/40',
          className
        )}
        {...props}
      />
      <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded bg-white px-1 text-sm text-slate-500 transition-all peer-focus:top-0 peer-focus:text-xs peer-focus:text-blue-600 peer-[:not(:placeholder-shown)]:top-0 peer-[:not(:placeholder-shown)]:text-xs">
        {label}
      </span>
      {error && <span className="mt-1 block text-xs text-red-600">{error}</span>}
    </label>
  )
}

export default FloatingField
