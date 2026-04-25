/**
 * SkillTree AI - Quest Skeleton Loader
 * Glass placeholders for loading state
 * @module components/quests/QuestSkeleton
 */

import { motion } from 'framer-motion';

/**
 * Quest Skeleton Component
 * @returns {JSX.Element}
 */
function QuestSkeleton() {
  return (
    <div className="glass-card p-6 rounded-2xl">
      <div className="animate-pulse">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-white/10" />
            <div className="w-16 h-4 rounded bg-white/10" />
          </div>
          <div className="w-24 h-6 rounded-full bg-white/10" />
        </div>

        {/* Title */}
        <div className="w-3/4 h-6 rounded bg-white/10 mb-2" />

        {/* Difficulty */}
        <div className="flex items-center gap-1 mb-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="w-1.5 h-1.5 rounded-full bg-white/10" />
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-white/5">
          <div className="flex items-center gap-4">
            <div className="w-16 h-4 rounded bg-white/10" />
            <div className="w-12 h-4 rounded bg-white/10" />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Quest List Skeleton Component
 * @param {Object} props
 * @param {number} props.count - Number of skeleton cards to show
 * @returns {JSX.Element}
 */
function QuestListSkeleton({ count = 6 }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[...Array(count)].map((_, index) => (
        <motion.div
          key={index}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: index * 0.05 }}
        >
          <QuestSkeleton />
        </motion.div>
      ))}
    </div>
  );
}

export default QuestListSkeleton;
export { QuestSkeleton };
