import React from 'react'
import { cn } from '../../lib/cn'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  glass?: boolean
}

const Card: React.FC<CardProps> = ({ className, glass = false, ...props }) => {
  return (
    <div
      className={cn(
        'rounded-2xl border border-slate-200/80 bg-white p-5 shadow-soft transition duration-200',
        glass && 'bg-white/70 backdrop-blur-xl',
        className
      )}
      {...props}
    />
  )
}

export default Card
