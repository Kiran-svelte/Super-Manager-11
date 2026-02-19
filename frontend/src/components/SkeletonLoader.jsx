// Skeleton Loader Component with Framer Motion
import React from 'react'
import { motion } from 'framer-motion'

export const SkeletonLoader = ({ variant = 'text', count = 1, className = '' }) => {
  const variants = {
    text: 'h-4 rounded',
    circle: 'h-12 w-12 rounded-full',
    rectangle: 'h-32 rounded-lg',
    card: 'h-48 rounded-xl',
  }

  const skeletonClass = variants[variant] || variants.text

  return (
    <div className={`space-y-3 ${className}`}>
      {[...Array(count)].map((_, i) => (
        <motion.div
          key={i}
          className={`bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 ${skeletonClass}`}
          animate={{
            backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
          }}
          transition={{
            duration: 2,
            ease: 'linear',
            repeat: Infinity,
          }}
          style={{
            backgroundSize: '200% 100%',
          }}
        />
      ))}
    </div>
  )
}

export const MessageSkeleton = () => (
  <div className="flex gap-3 p-4">
    <SkeletonLoader variant="circle" count={1} />
    <div className="flex-1 space-y-2">
      <SkeletonLoader variant="text" count={3} />
    </div>
  </div>
)

export const CardSkeleton = () => (
  <div className="p-6 space-y-4">
    <SkeletonLoader variant="text" count={1} className="w-1/2" />
    <SkeletonLoader variant="rectangle" count={1} />
    <div className="flex gap-2">
      <SkeletonLoader variant="text" count={1} className="w-20" />
      <SkeletonLoader variant="text" count={1} className="w-20" />
    </div>
  </div>
)

export default SkeletonLoader
