import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../../api/api';

const AssessmentsTab = () => {
  const [questions, setQuestions] = useState([]);
  const [quests, setQuests] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    quest: '',
    question_type: 'code',
    prompt: '',
    correct_answer: '',
    mcq_options: [],
    test_cases: [],
    validation_criteria: '',
    points: 10
  });

  useEffect(() => {
    fetchQuestions();
    fetchQuests();
  }, []);

  const fetchQuestions = async () => {
    try {
      const response = await api.get('/api/admin/questions/');
      const data = response.data;
      setQuestions(data.results || data);
    } catch (error) {
      console.error('Failed to fetch questions:', error);
    }
  };

  const fetchQuests = async () => {
    try {
      const response = await api.get('/api/admin/quests/');
      const data = response.data;
      setQuests(data.results || data);
    } catch (error) {
      console.error('Failed to fetch quests:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/api/admin/questions/', formData);
      setShowModal(false);
      setFormData({
        quest: '',
        question_type: 'code',
        prompt: '',
        correct_answer: '',
        mcq_options: [],
        test_cases: [],
        validation_criteria: '',
        points: 10
      });
      fetchQuestions();
    } catch (error) {
      console.error('Failed to create question:', error);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '28px', fontWeight: '700' }}>Assessment Questions</h2>
        <button
          onClick={() => setShowModal(true)}
          style={{
            padding: '12px 24px',
            background: 'linear-gradient(135deg, #7c6af5 0%, #9d8df7 100%)',
            border: 'none',
            borderRadius: '12px',
            color: '#fff',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          + Add Question
        </button>
      </div>

      <div style={{ display: 'grid', gap: '16px' }}>
        {questions.map(question => (
          <div
            key={question.id}
            style={{
              background: 'rgba(15, 18, 25, 0.6)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(124, 106, 245, 0.2)',
              borderRadius: '16px',
              padding: '20px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>
                  {question.quest_title}
                </h3>
                <span style={{
                  padding: '4px 12px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  background: 'rgba(124, 106, 245, 0.2)',
                  color: '#7c6af5'
                }}>
                  {question.question_type}
                </span>
              </div>
              <span style={{
                padding: '6px 12px',
                borderRadius: '12px',
                fontSize: '14px',
                fontWeight: '600',
                background: 'rgba(245, 158, 11, 0.2)',
                color: '#f59e0b'
              }}>
                {question.points} pts
              </span>
            </div>
            <p style={{ fontSize: '14px', color: '#9ca3af', lineHeight: '1.6' }}>
              {question.prompt.substring(0, 150)}...
            </p>
          </div>
        ))}
      </div>

      <AnimatePresence>
        {showModal && (
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
              zIndex: 1000
            }}
            onClick={() => setShowModal(false)}
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
                maxWidth: '700px',
                maxHeight: '90vh',
                overflowY: 'auto'
              }}
            >
              <h3 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '24px' }}>
                Add Assessment Question
              </h3>
              <form onSubmit={handleSubmit}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                      Quest
                    </label>
                    <select
                      value={formData.quest}
                      onChange={(e) => setFormData({ ...formData, quest: e.target.value })}
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
                      <option value="">Select Quest</option>
                      {quests.map(quest => (
                        <option key={quest.id} value={quest.id}>{quest.title}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                      Question Type
                    </label>
                    <select
                      value={formData.question_type}
                      onChange={(e) => setFormData({ ...formData, question_type: e.target.value })}
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
                      <option value="code">Code Challenge</option>
                      <option value="mcq">Multiple Choice</option>
                      <option value="open_ended">Open Ended</option>
                    </select>
                  </div>
                </div>
                <div style={{ marginBottom: '20px' }}>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                    Prompt
                  </label>
                  <textarea
                    value={formData.prompt}
                    onChange={(e) => setFormData({ ...formData, prompt: e.target.value })}
                    required
                    rows={4}
                    style={{
                      width: '100%',
                      padding: '12px',
                      background: 'rgba(15, 18, 25, 0.6)',
                      border: '1px solid rgba(124, 106, 245, 0.3)',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '14px',
                      resize: 'vertical'
                    }}
                  />
                </div>
                <div style={{ marginBottom: '20px' }}>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                    Validation Criteria
                  </label>
                  <textarea
                    value={formData.validation_criteria}
                    onChange={(e) => setFormData({ ...formData, validation_criteria: e.target.value })}
                    required
                    rows={3}
                    placeholder="Natural language criteria for AI evaluation..."
                    style={{
                      width: '100%',
                      padding: '12px',
                      background: 'rgba(15, 18, 25, 0.6)',
                      border: '1px solid rgba(124, 106, 245, 0.3)',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '14px',
                      resize: 'vertical'
                    }}
                  />
                </div>
                <div style={{ marginBottom: '20px' }}>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                    Points
                  </label>
                  <input
                    type="number"
                    value={formData.points}
                    onChange={(e) => setFormData({ ...formData, points: parseInt(e.target.value) })}
                    min="1"
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
                  />
                </div>
                <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    style={{
                      padding: '12px 24px',
                      background: 'rgba(124, 106, 245, 0.1)',
                      border: '1px solid rgba(124, 106, 245, 0.3)',
                      borderRadius: '8px',
                      color: '#fff',
                      cursor: 'pointer'
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
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
                    Create
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AssessmentsTab;
