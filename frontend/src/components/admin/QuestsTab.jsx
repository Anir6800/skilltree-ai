import React, { useState, useEffect } from 'react';
import useAuthStore from '../../store/authStore';
import { API_BASE_URL } from '../../constants';

const QuestsTab = () => {
  const { token } = useAuthStore();
  const [quests, setQuests] = useState([]);
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQuests();
    fetchSkills();
  }, []);

  const fetchQuests = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/quests/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      setQuests(data.results || data);
    } catch (error) {
      console.error('Failed to fetch quests:', error);
    } finally {
      setLoading(false);
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

  return (
    <div>
      <h2 style={{ fontSize: '28px', fontWeight: '700', marginBottom: '24px' }}>
        Quests Management
      </h2>
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
              <th style={{ padding: '16px', textAlign: 'left', fontWeight: '600' }}>Skill</th>
              <th style={{ padding: '16px', textAlign: 'left', fontWeight: '600' }}>Type</th>
              <th style={{ padding: '16px', textAlign: 'left', fontWeight: '600' }}>XP</th>
              <th style={{ padding: '16px', textAlign: 'left', fontWeight: '600' }}>Questions</th>
            </tr>
          </thead>
          <tbody>
            {quests.map(quest => (
              <tr key={quest.id} style={{ borderTop: '1px solid rgba(124, 106, 245, 0.1)' }}>
                <td style={{ padding: '16px' }}>{quest.title}</td>
                <td style={{ padding: '16px' }}>{quest.skill_title}</td>
                <td style={{ padding: '16px' }}>
                  <span style={{
                    padding: '4px 12px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    background: 'rgba(124, 106, 245, 0.2)',
                    color: '#7c6af5'
                  }}>
                    {quest.type}
                  </span>
                </td>
                <td style={{ padding: '16px' }}>{quest.xp_reward}</td>
                <td style={{ padding: '16px' }}>{quest.questions_count || 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default QuestsTab;
