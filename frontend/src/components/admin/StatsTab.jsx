import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import useAuthStore from '../../store/authStore';
import { API_BASE_URL } from '../../constants';

const StatsTab = () => {
  const { token } = useAuthStore();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/stats/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div style={{ color: '#9ca3af' }}>Loading stats...</div>;
  }

  const kpiCards = [
    { label: 'Published Skills', value: stats?.total_skills || 0, icon: '🎯', color: '#7c6af5' },
    { label: 'Total Quests', value: stats?.total_quests || 0, icon: '⚔️', color: '#f59e0b' },
    { label: 'Content Pieces', value: stats?.published_content || 0, icon: '📚', color: '#10b981' },
    { label: 'Pending Reviews', value: stats?.pending_review || 0, icon: '⏳', color: '#ef4444' },
  ];

  const chartData = stats?.content_by_category?.map(item => ({
    name: item.skill__category || 'Unknown',
    count: item.count
  })) || [];

  return (
    <div>
      <h2 style={{ fontSize: '28px', fontWeight: '700', marginBottom: '24px' }}>
        Dashboard Overview
      </h2>

      {/* KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '20px',
        marginBottom: '32px'
      }}>
        {kpiCards.map((kpi, idx) => (
          <motion.div
            key={kpi.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            style={{
              background: 'rgba(15, 18, 25, 0.6)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(124, 106, 245, 0.2)',
              borderRadius: '16px',
              padding: '24px',
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            <div style={{
              position: 'absolute',
              top: '-20px',
              right: '-20px',
              fontSize: '80px',
              opacity: 0.1
            }}>
              {kpi.icon}
            </div>
            <div style={{ position: 'relative', zIndex: 1 }}>
              <p style={{ fontSize: '14px', color: '#9ca3af', marginBottom: '8px' }}>
                {kpi.label}
              </p>
              <p style={{ fontSize: '36px', fontWeight: '700', color: kpi.color }}>
                {kpi.value}
              </p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Content by Category Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        style={{
          background: 'rgba(15, 18, 25, 0.6)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(124, 106, 245, 0.2)',
          borderRadius: '16px',
          padding: '24px',
          marginBottom: '32px'
        }}
      >
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>
          Content by Category
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(124, 106, 245, 0.1)" />
            <XAxis dataKey="name" stroke="#9ca3af" />
            <YAxis stroke="#9ca3af" />
            <Tooltip
              contentStyle={{
                background: 'rgba(15, 18, 25, 0.95)',
                border: '1px solid rgba(124, 106, 245, 0.3)',
                borderRadius: '8px',
                color: '#fff'
              }}
            />
            <Bar dataKey="count" fill="#7c6af5" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Recent Content */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        style={{
          background: 'rgba(15, 18, 25, 0.6)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(124, 106, 245, 0.2)',
          borderRadius: '16px',
          padding: '24px'
        }}
      >
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>
          Recent Content
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {stats?.recent_content?.slice(0, 5).map(content => (
            <div
              key={content.id}
              style={{
                padding: '16px',
                background: 'rgba(124, 106, 245, 0.05)',
                borderRadius: '8px',
                border: '1px solid rgba(124, 106, 245, 0.1)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
            >
              <div>
                <p style={{ fontWeight: '500', marginBottom: '4px' }}>{content.title}</p>
                <p style={{ fontSize: '14px', color: '#9ca3af' }}>
                  {content.skill_title} • {content.content_type}
                </p>
              </div>
              <span style={{
                padding: '4px 12px',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: '500',
                background: content.status === 'published' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                color: content.status === 'published' ? '#10b981' : '#f59e0b'
              }}>
                {content.status}
              </span>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default StatsTab;
