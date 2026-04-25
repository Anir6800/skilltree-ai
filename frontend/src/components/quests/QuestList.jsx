/**
 * SkillTree AI - Quest List Component
 * Responsive grid with animations
 * @module components/quests/QuestList
 */

import { motion } from 'framer-motion';
import QuestCard from './QuestCard';

/**
 * Quest List Component
 * @param {Object} props
 * @param {Array} props.quests - Array of quest objects
 * @param {Function} props.onQuestClick - Quest click handler
 * @returns {JSX.Element}
 */
function QuestList({ quests, onQuestClick }) {
  if (!quests || quests.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glass-panel p-12 rounded-2xl text-center"
      >
        <div className="text-6xl mb-4">🎯</div>
        <h3 className="text-xl font-bold text-white mb-2">No Quests Found</h3>
        <p className="text-slate-400">
          Try adjusting your filters or check back later for new quests.
        </p>
      </motion.div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {quests.map((quest, index) => (
        <motion.div
          key={quest.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05, duration: 0.3 }}
        >
          <QuestCard quest={quest} onClick={() => onQuestClick(quest)} />
        </motion.div>
      ))}
    </div>
  );
}

export default QuestList;
