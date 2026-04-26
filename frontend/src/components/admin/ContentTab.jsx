import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import useAuthStore from '../../store/authStore';
import { API_BASE_URL } from '../../constants';

const ContentTab = () => {
  const { token } = useAuthStore();
  const [content, setContent] = useState([]);
  const [skills, setSkills] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    skill: '',
    content_type: 'lesson',
    title: '',
    body: '',
    code_example: '',
    language: 'python'
  });
  const [previewMode, setPreviewMode] = useState(false);

  useEffect(() => {
    fetchContent();
    fetchSkills();
  }, []);

  const fetchContent = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/content/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      setContent(data.results || data);
    } catch (error) {
      console.error('Failed to fetch content:', error);
    }
  };

  const fetchSkills = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/skills/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      setSkills(data.results || data);
    } catch (error) {
      console.error('Failed to fetch skills:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE_URL}/admin/content/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setShowModal(false);
        setFormData({
          skill: '',
          content_type: 'lesson',
          title: '',
          body: '',
          code_example: '',
          language: 'python'
        });
        fetchContent();
      }
    } catch (error) {
      console.error('Failed to create content:', error);
    }
  };

  const handlePublish = async (id) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/content/${id}/publish/`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        fetchContent();
        alert('Content reviewed and published!');
      }
    } catch (error) {
      console.error('Failed to publish content:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'published': return { bg: 'rgba(16, 185, 129, 0.2)', color: '#10b981' };
      case 'ai_reviewed': return { bg: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b' };
      default: return { bg: 'rgba(156, 163, 175, 0.2)', color: '#9ca3af' };
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '28px', fontWeight: '700' }}>Content Library</h2>
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
          + Add Lesson
        </button>
      </div>

      <div style={{ display: 'grid', gap: '16px' }}>
        {content.map(item => {
          const statusStyle = getStatusColor(item.status);
          return (
            <div
              key={item.id}
              style={{
                background: 'rgba(15, 18, 25, 0.6)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(124, 106, 245, 0.2)',
                borderRadius: '16px',
                padding: '20px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
            >
              <div style={{ flex: 1 }}>
                <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
                  {item.title}
                </h3>
                <p style={{ fontSize: '14px', color: '#9ca3af', marginBottom: '8px' }}>
                  {item.skill_title} • {item.content_type}
                </p>
                <span style={{
                  padding: '4px 12px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: '500',
                  background: statusStyle.bg,
                  color: statusStyle.color
                }}>
                  {item.status}
                </span>
              </div>
              {item.status === 'draft' && (
                <button
                  onClick={() => handlePublish(item.id)}
                  style={{
                    padding: '8px 16px',
                    background: 'rgba(124, 106, 245, 0.2)',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#7c6af5',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}
                >
                  Review & Publish
                </button>
              )}
            </div>
          );
        })}
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
                maxWidth: '900px',
                maxHeight: '90vh',
                overflowY: 'auto'
              }}
            >
              <h3 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '24px' }}>
                Add New Content
              </h3>
              <form onSubmit={handleSubmit}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                      Skill
                    </label>
                    <select
                      value={formData.skill}
                      onChange={(e) => setFormData({ ...formData, skill: e.target.value })}
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
                      Content Type
                    </label>
                    <select
                      value={formData.content_type}
                      onChange={(e) => setFormData({ ...formData, content_type: e.target.value })}
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
                      <option value="lesson">Lesson</option>
                      <option value="tip">Tip</option>
                      <option value="example">Example</option>
                      <option value="reference">Reference</option>
                    </select>
                  </div>
                </div>
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
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <label style={{ fontSize: '14px', fontWeight: '500' }}>
                      Body (Markdown)
                    </label>
                    <button
                      type="button"
                      onClick={() => setPreviewMode(!previewMode)}
                      style={{
                        padding: '4px 12px',
                        background: 'rgba(124, 106, 245, 0.2)',
                        border: 'none',
                        borderRadius: '6px',
                        color: '#7c6af5',
                        fontSize: '12px',
                        cursor: 'pointer'
                      }}
                    >
                      {previewMode ? 'Edit' : 'Preview'}
                    </button>
                  </div>
                  {previewMode ? (
                    <div style={{
                      padding: '12px',
                      background: 'rgba(15, 18, 25, 0.6)',
                      border: '1px solid rgba(124, 106, 245, 0.3)',
                      borderRadius: '8px',
                      minHeight: '200px',
                      color: '#fff'
                    }}>
                      {formData.body || 'No content yet...'}
                    </div>
                  ) : (
                    <textarea
                      value={formData.body}
                      onChange={(e) => setFormData({ ...formData, body: e.target.value })}
                      required
                      rows={8}
                      style={{
                        width: '100%',
                        padding: '12px',
                        background: 'rgba(15, 18, 25, 0.6)',
                        border: '1px solid rgba(124, 106, 245, 0.3)',
                        borderRadius: '8px',
                        color: '#fff',
                        fontSize: '14px',
                        resize: 'vertical',
                        fontFamily: 'monospace'
                      }}
                    />
                  )}
                </div>
                <div style={{ marginBottom: '20px' }}>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                    Code Example (Optional)
                  </label>
                  <textarea
                    value={formData.code_example}
                    onChange={(e) => setFormData({ ...formData, code_example: e.target.value })}
                    rows={6}
                    style={{
                      width: '100%',
                      padding: '12px',
                      background: 'rgba(15, 18, 25, 0.6)',
                      border: '1px solid rgba(124, 106, 245, 0.3)',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '14px',
                      resize: 'vertical',
                      fontFamily: 'monospace'
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

export default ContentTab;
