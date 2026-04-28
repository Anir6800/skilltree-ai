import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import api from '../api/api';

const WeeklyReportWidget = () => {
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [unviewedCount, setUnviewedCount] = useState(0);

  useEffect(() => {
    fetchLatestReport();
  }, []);

  const fetchLatestReport = async () => {
    try {
      const response = await api.get('/api/reports/latest/');
      setReport(response.data);
    } catch (error) {
      console.error('Failed to fetch latest report:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api.get('/api/reports/stats/');
      setUnviewedCount(response.data.unviewed_count);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading || !report) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        background: 'linear-gradient(135deg, rgba(124, 106, 245, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%)',
        border: '1px solid rgba(124, 106, 245, 0.3)',
        borderRadius: '16px',
        padding: '20px',
        backdropFilter: 'blur(20px)',
        cursor: 'pointer',
        transition: 'all 0.3s ease'
      }}
      onClick={() => navigate('/reports')}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'rgba(124, 106, 245, 0.6)';
        e.currentTarget.style.background = 'linear-gradient(135deg, rgba(124, 106, 245, 0.15) 0%, rgba(16, 185, 129, 0.1) 100%)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'rgba(124, 106, 245, 0.3)';
        e.currentTarget.style.background = 'linear-gradient(135deg, rgba(124, 106, 245, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%)';
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#fff' }}>
          📊 Your Week in Review
        </h3>
        {unviewedCount > 0 && (
          <span style={{
            background: '#ef4444',
            color: '#fff',
            fontSize: '12px',
            fontWeight: '700',
            padding: '4px 8px',
            borderRadius: '12px'
          }}>
            {unviewedCount} new
          </span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '12px' }}>
        <div>
          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>XP Earned</div>
          <div style={{ fontSize: '18px', fontWeight: '700', color: '#10b981' }}>
            {report.data?.xp_earned || 0}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>Quests Passed</div>
          <div style={{ fontSize: '18px', fontWeight: '700', color: '#3b82f6' }}>
            {report.data?.quests_passed || 0}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>Win Rate</div>
          <div style={{ fontSize: '18px', fontWeight: '700', color: '#f59e0b' }}>
            {report.data?.win_rate || 0}%
          </div>
        </div>
      </div>

      <button
        style={{
          width: '100%',
          padding: '10px',
          background: 'linear-gradient(135deg, #7c6af5 0%, #9d8df7 100%)',
          border: 'none',
          borderRadius: '8px',
          color: '#fff',
          fontWeight: '600',
          cursor: 'pointer',
          fontSize: '14px'
        }}
      >
        Download Full PDF →
      </button>
    </motion.div>
  );
};

export default WeeklyReportWidget;
