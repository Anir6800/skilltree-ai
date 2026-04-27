import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../../api/api';

const SkillsTab = () => {
  const [skills, setSkills] = useState([]);
  const [allSkills, setAllSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingSkill, setEditingSkill] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'algorithms',
    difficulty: 1,
    xp_required_to_unlock: 0,
    prerequisites: []
  });

  useEffect(() => {
    fetchSkills();
  }, []);

  const fetchSkills = async () => {
    try {
      const response = await api.get('/api/admin/skills/');
      const data = response.data;
      setSkills(data.results || data);
      setAllSkills(data.results || data);
    } catch (error) {
      console.error('Failed to fetch skills:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (term) => {
    setSearchTerm(term);
    if (!term) {
      setSkills(allSkills);
    } else {
      setSkills(allSkills.filter(s =>
        s.title.toLowerCase().includes(term.toLowerCase()) ||
        s.description.toLowerCase().includes(term.toLowerCase())
      ));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingSkill) {
        await api.put(`/api/admin/skills/${editingSkill.id}/`, formData);
      } else {
        await api.post('/api/admin/skills/', formData);
      }
      setShowModal(false);
      setEditingSkill(null);
      setFormData({
        title: '',
        description: '',
        category: 'algorithms',
        difficulty: 1,
        xp_required_to_unlock: 0,
        prerequisites: []
      });
      fetchSkills();
    } catch (error) {
      console.error('Failed to save skill:', error);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this skill? This will cascade to all related quests.')) return;
    try {
      await api.delete(`/api/admin/skills/${id}/`);
      fetchSkills();
    } catch (error) {
      console.error('Failed to delete skill:', error);
    }
  };

  const openEditModal = (skill) => {
    setEditingSkill(skill);
    setFormData({
      title: skill.title,
      description: skill.description,
      category: skill.category,
      difficulty: skill.difficulty,
      xp_required_to_unlock: skill.xp_required_to_unlock,
      prerequisites: skill.prerequisites || []
    });
    setShowModal(true);
  };

  const categories = [
    { value: 'algorithms', label: 'Algorithms' },
    { value: 'ds', label: 'Data Structures' },
    { value: 'systems', label: 'Systems' },
    { value: 'webdev', label: 'Web Development' },
    { value: 'aiml', label: 'AI/ML' }
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '28px', fontWeight: '700' }}>Skills Management</h2>
        <button
          onClick={() => {
            setEditingSkill(null);
            setFormData({
              title: '',
              description: '',
              category: 'algorithms',
              difficulty: 1,
              xp_required_to_unlock: 0,
              prerequisites: []
            });
            setShowModal(true);
          }}
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
          + Add Skill
        </button>
      </div>

      <input
        type="text"
        placeholder="Search skills..."
        value={searchTerm}
        onChange={(e) => handleSearch(e.target.value)}
        style={{
          width: '100%',
          padding: '12px 16px',
          background: 'rgba(15, 18, 25, 0.6)',
          border: '1px solid rgba(124, 106, 245, 0.3)',
          borderRadius: '12px',
          color: '#fff',
          marginBottom: '24px',
          fontSize: '14px'
        }}
      />

      <div style={{
        background: 'rgba(15, 18, 25, 0.6)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(124, 106, 245, 0.2)',
        borderRadius: '16px',
        overflow: 'hidden'
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'rgba(124, 106, 245, 0.1)' }}>
              <th style={{ padding: '16px', textAlign: 'left', fontWeight: '600' }}>Title</th>
              <th style={{ padding: '16px', textAlign: 'left', fontWeight: '600' }}>Category</th>
              <th style={{ padding: '16px', textAlign: 'left', fontWeight: '600' }}>Difficulty</th>
              <th style={{ padding: '16px', textAlign: 'left', fontWeight: '600' }}>Quests</th>
              <th style={{ padding: '16px', textAlign: 'left', fontWeight: '600' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {skills.map(skill => (
              <tr key={skill.id} style={{ borderTop: '1px solid rgba(124, 106, 245, 0.1)' }}>
                <td style={{ padding: '16px' }}>{skill.title}</td>
                <td style={{ padding: '16px' }}>
                  <span style={{
                    padding: '4px 12px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    background: 'rgba(124, 106, 245, 0.2)',
                    color: '#7c6af5'
                  }}>
                    {skill.category}
                  </span>
                </td>
                <td style={{ padding: '16px' }}>{skill.difficulty}/5</td>
                <td style={{ padding: '16px' }}>{skill.quests_count || 0}</td>
                <td style={{ padding: '16px' }}>
                  <button
                    onClick={() => openEditModal(skill)}
                    style={{
                      padding: '6px 12px',
                      background: 'rgba(124, 106, 245, 0.2)',
                      border: 'none',
                      borderRadius: '8px',
                      color: '#7c6af5',
                      cursor: 'pointer',
                      marginRight: '8px',
                      fontSize: '12px'
                    }}
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(skill.id)}
                    style={{
                      padding: '6px 12px',
                      background: 'rgba(239, 68, 68, 0.2)',
                      border: 'none',
                      borderRadius: '8px',
                      color: '#ef4444',
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
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
                maxWidth: '600px',
                maxHeight: '90vh',
                overflowY: 'auto'
              }}
            >
              <h3 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '24px' }}>
                {editingSkill ? 'Edit Skill' : 'Add New Skill'}
              </h3>
              <form onSubmit={handleSubmit}>
                <div style={{ marginBottom: '20px' }}>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                    Title
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
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
                <div style={{ marginBottom: '20px' }}>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
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
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                      Category
                    </label>
                    <select
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value })}
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
                      {categories.map(cat => (
                        <option key={cat.value} value={cat.value}>{cat.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                      Difficulty (1-5)
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="5"
                      value={formData.difficulty}
                      onChange={(e) => setFormData({ ...formData, difficulty: parseInt(e.target.value) })}
                      style={{ width: '100%' }}
                    />
                    <div style={{ textAlign: 'center', color: '#7c6af5', fontWeight: '600' }}>
                      {formData.difficulty}
                    </div>
                  </div>
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
                    {editingSkill ? 'Update' : 'Create'}
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

export default SkillsTab;
