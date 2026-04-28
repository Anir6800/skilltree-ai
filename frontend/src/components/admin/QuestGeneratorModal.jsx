import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../../api/api';

const QuestGeneratorModal = ({ isOpen, onClose, skills, onQuestSaved }) => {
  const [generatingQuests, setGeneratingQuests] = useState(false);
  const [generatedQuests, setGeneratedQuests] = useState([]);
  const [lmStudioAvailable, setLmStudioAvailable] = useState(false);
  
  const [generateFormData, setGenerateFormData] = useState({
    skill_id: '',
    topic_hint: '',
    difficulty: 3,
    quest_type: 'coding',
    batch_count: 1
  });

  useEffect(() => {
    if (isOpen) {
      checkLmStudioStatus();
    }
  }, [isOpen]);

  const checkLmStudioStatus = async () => {
    try {
      const response = await api.get('/api/admin/quests/lm-studio-status/');
      setLmStudioAvailable(response.data.available);
    } catch (error) {
      console.error('Failed to check LM Studio status:', error);
      setLmStudioAvailable(false);
    }
  };

  const handleGenerateQuest = async (e) => {
    e.preventDefault();
    setGeneratingQuests(true);

    try {
      if (generateFormData.batch_count > 1) {
        const response = await api.post('/api/admin/quests/generate-batch/', {
          skill_id: parseInt(generateFormData.skill_id),
          topic_hint: generateFormData.topic_hint,
          difficulty: generateFormData.difficulty,
          quest_type: generateFormData.quest_type,
          count: generateFormData.batch_count
        });
        setGeneratedQuests(response.data.quests);
      } else {
        const response = await api.post('/api/admin/quests/generate/', {
          skill_id: parseInt(generateFormData.skill_id),
          topic_hint: generateFormData.topic_hint,
          difficulty: generateFormData.difficulty,
          quest_type: generateFormData.quest_type
        });
        setGeneratedQuests([response.data.quest_data]);
      }
    } catch (error) {
      console.error('Failed to generate quests:', error);
      alert('Failed to generate quests: ' + (error.response?.data?.error || error.message));
    } finally {
      setGeneratingQuests(false);
    }
  };

  const handleSaveQuestDraft = async (questData) => {
    try {
      const response = await api.post('/api/admin/quests/save-draft/', {
        skill_id: parseInt(generateFormData.skill_id),
        quest_data: questData
      });
      alert(`Quest saved as draft: ${response.data.title}`);
      setGeneratedQuests([]);
      onQuestSaved();
    } catch (error) {
      console.error('Failed to save quest:', error);
      alert('Failed to save quest: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleClose = () => {
    setGeneratedQuests([]);
    setGenerateFormData({
      skill_id: '',
      topic_hint: '',
      difficulty: 3,
      quest_type: 'coding',
      batch_count: 1
    });
    onClose();
  };

  if (!lmStudioAvailable) {
    return null;
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            overflowY: 'auto'
          }}
          onClick={handleClose}
        >
          <motion.div
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'linear-gradient(135deg, #1a1d29 0%, #0f1219 100%)',
              border: '1px solid rgba(124, 106, 245, 0.3)',
              borderRadius: '16px',
              padding: '32px',
              width: '90%',
              maxWidth: '900px',
              maxHeight: '90vh',
              overflowY: 'auto',
              margin: '20px auto'
            }}
          >
            {generatedQuests.length === 0 ? (
              <>
                <h3 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '24px' }}>
                  ✦ Generate Quests with AI
                </h3>
                <form onSubmit={handleGenerateQuest}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                    <div>
                      <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                        Skill
                      </label>
                      <select
                        value={generateFormData.skill_id}
                        onChange={(e) => setGenerateFormData({ ...generateFormData, skill_id: e.target.value })}
                        required
                        style={{
                          width: '100%',
                          padding: '12px',
                          background: 'rgba(15, 18, 25, 0.6)',
                          border: '1px solid rgba(124, 106, 245, 0.3)',
                          borderRadius: '8px',
                          color: '#fff',
                          fontSize: '14px'
                        }}
                      >
                        <option value="">Select Skill</option>
                        {skills.map(skill => (
                          <option key={skill.id} value={skill.id}>{skill.title}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                        Quest Type
                      </label>
                      <select
                        value={generateFormData.quest_type}
                        onChange={(e) => setGenerateFormData({ ...generateFormData, quest_type: e.target.value })}
                        style={{
                          width: '100%',
                          padding: '12px',
                          background: 'rgba(15, 18, 25, 0.6)',
                          border: '1px solid rgba(124, 106, 245, 0.3)',
                          borderRadius: '8px',
                          color: '#fff',
                          fontSize: '14px'
                        }}
                      >
                        <option value="coding">Coding</option>
                        <option value="debugging">Debugging</option>
                        <option value="mcq">Multiple Choice</option>
                      </select>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                    <div>
                      <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                        Difficulty (1-5)
                      </label>
                      <input
                        type="range"
                        min="1"
                        max="5"
                        value={generateFormData.difficulty}
                        onChange={(e) => setGenerateFormData({ ...generateFormData, difficulty: parseInt(e.target.value) })}
                        style={{
                          width: '100%',
                          cursor: 'pointer'
                        }}
                      />
                      <div style={{ textAlign: 'center', marginTop: '8px', fontSize: '14px', color: '#9ca3af' }}>
                        Level {generateFormData.difficulty}
                      </div>
                    </div>
                    <div>
                      <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                        Number of Quests
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="10"
                        value={generateFormData.batch_count}
                        onChange={(e) => setGenerateFormData({ ...generateFormData, batch_count: parseInt(e.target.value) })}
                        style={{
                          width: '100%',
                          padding: '12px',
                          background: 'rgba(15, 18, 25, 0.6)',
                          border: '1px solid rgba(124, 106, 245, 0.3)',
                          borderRadius: '8px',
                          color: '#fff',
                          fontSize: '14px'
                        }}
                      />
                    </div>
                  </div>

                  <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                      Topic Hint (Optional)
                    </label>
                    <input
                      type="text"
                      value={generateFormData.topic_hint}
                      onChange={(e) => setGenerateFormData({ ...generateFormData, topic_hint: e.target.value })}
                      placeholder="e.g., Two Pointers, Dynamic Programming..."
                      style={{
                        width: '100%',
                        padding: '12px',
                        background: 'rgba(15, 18, 25, 0.6)',
                        border: '1px solid rgba(124, 106, 245, 0.3)',
                        borderRadius: '8px',
                        color: '#fff',
                        fontSize: '14px'
                      }}
                    />
                  </div>

                  <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                    <button
                      type="button"
                      onClick={handleClose}
                      disabled={generatingQuests}
                      style={{
                        padding: '12px 24px',
                        background: 'rgba(124, 106, 245, 0.1)',
                        border: '1px solid rgba(124, 106, 245, 0.3)',
                        borderRadius: '8px',
                        color: '#fff',
                        cursor: generatingQuests ? 'not-allowed' : 'pointer',
                        opacity: generatingQuests ? 0.5 : 1
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={generatingQuests}
                      style={{
                        padding: '12px 24px',
                        background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                        border: 'none',
                        borderRadius: '8px',
                        color: '#fff',
                        fontWeight: '600',
                        cursor: generatingQuests ? 'not-allowed' : 'pointer',
                        opacity: generatingQuests ? 0.7 : 1
                      }}
                    >
                      {generatingQuests ? 'Generating...' : 'Generate'}
                    </button>
                  </div>
                </form>
              </>
            ) : (
              <>
                <h3 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '24px' }}>
                  Generated Quests Preview ({generatedQuests.length})
                </h3>
                <div style={{ display: 'grid', gap: '16px', marginBottom: '24px' }}>
                  {generatedQuests.map((quest, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      style={{
                        background: 'rgba(15, 18, 25, 0.6)',
                        border: '1px solid rgba(124, 106, 245, 0.2)',
                        borderRadius: '12px',
                        padding: '16px'
                      }}
                    >
                      <div style={{ marginBottom: '12px' }}>
                        <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>
                          {quest.title}
                        </h4>
                        <p style={{ fontSize: '13px', color: '#9ca3af', lineHeight: '1.5' }}>
                          {quest.description.substring(0, 200)}...
                        </p>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '12px', fontSize: '12px' }}>
                        <div style={{ background: 'rgba(124, 106, 245, 0.1)', padding: '8px', borderRadius: '6px' }}>
                          <div style={{ color: '#9ca3af' }}>XP Reward</div>
                          <div style={{ color: '#10b981', fontWeight: '600' }}>{quest.xp_reward}</div>
                        </div>
                        <div style={{ background: 'rgba(124, 106, 245, 0.1)', padding: '8px', borderRadius: '6px' }}>
                          <div style={{ color: '#9ca3af' }}>Time</div>
                          <div style={{ color: '#10b981', fontWeight: '600' }}>{quest.estimated_minutes}m</div>
                        </div>
                        <div style={{ background: 'rgba(124, 106, 245, 0.1)', padding: '8px', borderRadius: '6px' }}>
                          <div style={{ color: '#9ca3af' }}>Tests</div>
                          <div style={{ color: '#10b981', fontWeight: '600' }}>{quest.test_cases?.length || 0}</div>
                        </div>
                        <div style={{ background: 'rgba(124, 106, 245, 0.1)', padding: '8px', borderRadius: '6px' }}>
                          <div style={{ color: '#9ca3af' }}>Type</div>
                          <div style={{ color: '#10b981', fontWeight: '600' }}>{quest.type}</div>
                        </div>
                      </div>
                      <button
                        onClick={() => handleSaveQuestDraft(quest)}
                        style={{
                          width: '100%',
                          padding: '10px',
                          background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                          border: 'none',
                          borderRadius: '8px',
                          color: '#fff',
                          fontWeight: '600',
                          cursor: 'pointer',
                          fontSize: '14px'
                        }}
                      >
                        Save as Draft
                      </button>
                    </motion.div>
                  ))}
                </div>
                <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                  <button
                    onClick={() => setGeneratedQuests([])}
                    style={{
                      padding: '12px 24px',
                      background: 'rgba(124, 106, 245, 0.1)',
                      border: '1px solid rgba(124, 106, 245, 0.3)',
                      borderRadius: '8px',
                      color: '#fff',
                      cursor: 'pointer'
                    }}
                  >
                    Generate More
                  </button>
                  <button
                    onClick={handleClose}
                    style={{
                      padding: '12px 24px',
                      background: 'linear-gradient(135deg, #7c6af5 0%, #9d8df7 100%)',
                      border: 'none',
                      borderRadius: '8px',
                      color: '#fff',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    Close
                  </button>
                </div>
              </>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default QuestGeneratorModal;
