import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import useAuthStore from '../store/authStore';
import { API_BASE_URL } from '../constants';
import SkillsTab from '../components/admin/SkillsTab';
import QuestsTab from '../components/admin/QuestsTab';
import ContentTab from '../components/admin/ContentTab';
import AssessmentsTab from '../components/admin/AssessmentsTab';
import StatsTab from '../components/admin/StatsTab';

const AdminPage = () => {
  const { user, token } = useAuthStore();
  const [activeTab, setActiveTab] = useState('stats');
  const [loading, setLoading] = useState(false);

  if (!user?.is_staff) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0a0c10 0%, #1a1d29 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff'
      }}>
        <div style={{ textAlign: 'center' }}>
          <h1 style={{ fontSize: '24px', marginBottom: '16px' }}>Access Denied</h1>
          <p style={{ color: '#9ca3af' }}>Admin privileges required</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'stats', label: 'Dashboard', icon: '📊' },
    { id: 'skills', label: 'Skills', icon: '🎯' },
    { id: 'quests', label: 'Quests', icon: '⚔️' },
    { id: 'content', label: 'Content Library', icon: '📚' },
    { id: 'assessments', label: 'Assessments', icon: '✅' },
  ];

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0a0c10 0%, #1a1d29 100%)',
      color: '#fff',
      display: 'flex'
    }}>
      {/* Sidebar */}
      <div style={{
        width: '240px',
        background: 'rgba(15, 18, 25, 0.8)',
        backdropFilter: 'blur(20px)',
        borderRight: '1px solid rgba(124, 106, 245, 0.1)',
        padding: '24px 0',
        position: 'fixed',
        height: '100vh',
        overflowY: 'auto'
      }}>
        <div style={{ padding: '0 24px', marginBottom: '32px' }}>
          <h1 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '8px' }}>
            Admin Panel
          </h1>
          <p style={{ fontSize: '14px', color: '#9ca3af' }}>
            Content Management
          </p>
        </div>

        <nav>
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                width: '100%',
                padding: '12px 24px',
                background: activeTab === tab.id ? 'rgba(124, 106, 245, 0.15)' : 'transparent',
                border: 'none',
                borderLeft: activeTab === tab.id ? '3px solid #7c6af5' : '3px solid transparent',
                color: activeTab === tab.id ? '#7c6af5' : '#9ca3af',
                fontSize: '14px',
                fontWeight: '500',
                textAlign: 'left',
                cursor: 'pointer',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '12px'
              }}
            >
              <span style={{ fontSize: '18px' }}>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Main Content */}
      <div style={{ marginLeft: '240px', flex: 1, padding: '32px' }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            {activeTab === 'stats' && <StatsTab />}
            {activeTab === 'skills' && <SkillsTab />}
            {activeTab === 'quests' && <QuestsTab />}
            {activeTab === 'content' && <ContentTab />}
            {activeTab === 'assessments' && <AssessmentsTab />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

export default AdminPage;
