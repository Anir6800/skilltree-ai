import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import useAuthStore from '../../store/authStore';
import { API_BASE_URL } from '../../constants';

const FlaggedSubmissionsTab = () => {
  const { token } = useAuthStore();
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedId, setExpandedId] = useState(null);
  const [actionLoading, setActionLoading] = useState({});
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    fetchFlaggedSubmissions();
  }, [statusFilter]);

  const fetchFlaggedSubmissions = async () => {
    setLoading(true);
    setError('');

    try {
      const url = new URL(`${API_BASE_URL}/ai-detection/admin/flagged-submissions/`);
      if (statusFilter !== 'all') {
        url.searchParams.append('status', statusFilter);
      }

      const response = await fetch(url.toString(), {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch flagged submissions');
      }

      const data = await response.json();
      setSubmissions(data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (submissionId, action, adminNote = '') => {
    setActionLoading((prev) => ({ ...prev, [submissionId]: true }));

    try {
      const response = await fetch(
        `${API_BASE_URL}/ai-detection/admin/submissions/${submissionId}/review/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ action, admin_note: adminNote }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to review submission');
      }

      // Refresh list
      fetchFlaggedSubmissions();
    } catch (err) {
      setError(err.message);
    } finally {
      setActionLoading((prev) => ({ ...prev, [submissionId]: false }));
    }
  };

  const getStatusColor = (status) => {
    if (status === 'flagged') return { bg: 'rgba(239, 68, 68, 0.1)', border: '#ef4444', text: '#fca5a5' };
    if (status === 'explanation_provided') return { bg: 'rgba(245, 158, 11, 0.1)', border: '#f59e0b', text: '#fbbf24' };
    if (status === 'approved') return { bg: 'rgba(16, 185, 129, 0.1)', border: '#10b981', text: '#6ee7b7' };
    if (status === 'confirmed_ai') return { bg: 'rgba(239, 68, 68, 0.15)', border: '#dc2626', text: '#fca5a5' };
    return { bg: 'rgba(16, 185, 129, 0.1)', border: '#10b981', text: '#6ee7b7' };
  };

  const getStatusIcon = (status) => {
    if (status === 'flagged') return <AlertCircle size={16} />;
    if (status === 'explanation_provided') return <AlertCircle size={16} />;
    if (status === 'approved') return <CheckCircle size={16} />;
    if (status === 'confirmed_ai') return <XCircle size={16} />;
    return <CheckCircle size={16} />;
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <div style={{ fontSize: '14px', color: '#9ca3af' }}>Loading flagged submissions...</div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#fff', marginBottom: '8px' }}>
          Flagged Submissions
        </h2>
        <p style={{ fontSize: '14px', color: '#9ca3af' }}>
          Review submissions flagged by the AI detection system
        </p>
      </div>

      {/* Filters */}
      <div style={{ marginBottom: '24px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        {['all', 'flagged', 'explanation_provided', 'approved', 'confirmed_ai'].map((filter) => (
          <motion.button
            key={filter}
            onClick={() => setStatusFilter(filter)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            style={{
              background:
                statusFilter === filter
                  ? 'linear-gradient(135deg, #7c6af5 0%, #a78bfa 100%)'
                  : 'rgba(255, 255, 255, 0.1)',
              border: statusFilter === filter ? 'none' : '1px solid rgba(255, 255, 255, 0.2)',
              color: '#fff',
              borderRadius: '8px',
              padding: '8px 16px',
              fontSize: '13px',
              fontWeight: '500',
              cursor: 'pointer',
              textTransform: 'capitalize',
              transition: 'all 0.2s',
            }}
          >
            {filter === 'all' ? 'All' : filter.replace('_', ' ')}
          </motion.button>
        ))}
      </div>

      {/* Error Message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '16px',
            fontSize: '13px',
            color: '#fca5a5',
          }}
        >
          {error}
        </motion.div>
      )}

      {/* Submissions List */}
      {submissions.length === 0 ? (
        <div
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '12px',
            padding: '40px',
            textAlign: 'center',
          }}
        >
          <CheckCircle size={40} color='#10b981' style={{ margin: '0 auto 16px' }} />
          <p style={{ fontSize: '14px', color: '#9ca3af' }}>No flagged submissions</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {submissions.map((submission) => {
            const statusColor = getStatusColor(submission.status);
            const isExpanded = expandedId === submission.id;

            return (
              <motion.div
                key={submission.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                style={{
                  background: statusColor.bg,
                  border: `1px solid ${statusColor.border}`,
                  borderRadius: '12px',
                  overflow: 'hidden',
                }}
              >
                {/* Row Header */}
                <motion.button
                  onClick={() => setExpandedId(isExpanded ? null : submission.id)}
                  style={{
                    width: '100%',
                    background: 'transparent',
                    border: 'none',
                    padding: '16px',
                    textAlign: 'left',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <div style={{ color: statusColor.text }}>{getStatusIcon(submission.status)}</div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '14px', fontWeight: '600', color: '#fff' }}>
                        {submission.user.username}
                      </span>
                      <span style={{ fontSize: '12px', color: '#9ca3af' }}>
                        {submission.quest.title}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                      Score: {Math.round(submission.ai_detection_score * 100)}% •{' '}
                      {new Date(submission.created_at).toLocaleDateString()}
                    </div>
                  </div>

                  <div style={{ color: statusColor.text }}>
                    {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </div>
                </motion.button>

                {/* Expanded Content */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.2 }}
                      style={{
                        borderTop: `1px solid ${statusColor.border}`,
                        padding: '16px',
                      }}
                    >
                      {/* Detection Scores */}
                      {submission.detection_log && (
                        <div style={{ marginBottom: '16px' }}>
                          <div style={{ fontSize: '12px', fontWeight: '600', color: '#d1d5db', marginBottom: '8px' }}>
                            Detection Breakdown
                          </div>
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                            <ScoreBox
                              label='Embedding'
                              score={submission.detection_log.embedding_score}
                            />
                            <ScoreBox label='LLM' score={submission.detection_log.llm_score} />
                            <ScoreBox
                              label='Heuristic'
                              score={submission.detection_log.heuristic_score}
                            />
                          </div>
                        </div>
                      )}

                      {/* LLM Reasoning */}
                      {submission.detection_log?.llm_reasoning && (
                        <div style={{ marginBottom: '16px' }}>
                          <div style={{ fontSize: '12px', fontWeight: '600', color: '#d1d5db', marginBottom: '6px' }}>
                            LLM Analysis
                          </div>
                          <div style={{ fontSize: '12px', color: '#9ca3af', lineHeight: '1.5' }}>
                            {submission.detection_log.llm_reasoning.reasoning || 'No reasoning provided'}
                          </div>
                        </div>
                      )}

                      {/* User Explanation */}
                      {submission.explanation && (
                        <div style={{ marginBottom: '16px' }}>
                          <div style={{ fontSize: '12px', fontWeight: '600', color: '#d1d5db', marginBottom: '6px' }}>
                            User Explanation
                          </div>
                          <div
                            style={{
                              fontSize: '12px',
                              color: '#9ca3af',
                              lineHeight: '1.5',
                              background: 'rgba(255, 255, 255, 0.05)',
                              padding: '8px',
                              borderRadius: '6px',
                              maxHeight: '150px',
                              overflowY: 'auto',
                            }}
                          >
                            {submission.explanation}
                          </div>
                        </div>
                      )}

                      {/* Code Preview */}
                      <div style={{ marginBottom: '16px' }}>
                        <div style={{ fontSize: '12px', fontWeight: '600', color: '#d1d5db', marginBottom: '6px' }}>
                          Code Preview ({submission.code_full_length} chars)
                        </div>
                        <pre
                          style={{
                            background: 'rgba(0, 0, 0, 0.3)',
                            padding: '8px',
                            borderRadius: '6px',
                            fontSize: '11px',
                            color: '#9ca3af',
                            overflow: 'auto',
                            maxHeight: '200px',
                            margin: 0,
                          }}
                        >
                          {submission.code}
                        </pre>
                      </div>

                      {/* Action Buttons */}
                      <div style={{ display: 'flex', gap: '8px' }}>
                        {submission.status !== 'approved' && submission.status !== 'confirmed_ai' && (
                          <>
                            <motion.button
                              onClick={() => handleReview(submission.id, 'approve')}
                              disabled={actionLoading[submission.id]}
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                              style={{
                                flex: 1,
                                background: 'rgba(16, 185, 129, 0.2)',
                                border: '1px solid #10b981',
                                color: '#6ee7b7',
                                borderRadius: '6px',
                                padding: '8px',
                                fontSize: '12px',
                                fontWeight: '600',
                                cursor: actionLoading[submission.id] ? 'not-allowed' : 'pointer',
                                transition: 'all 0.2s',
                                opacity: actionLoading[submission.id] ? 0.5 : 1,
                              }}
                            >
                              {actionLoading[submission.id] ? 'Processing...' : '✓ Approve'}
                            </motion.button>
                            <motion.button
                              onClick={() => handleReview(submission.id, 'override')}
                              disabled={actionLoading[submission.id]}
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                              style={{
                                flex: 1,
                                background: 'rgba(239, 68, 68, 0.2)',
                                border: '1px solid #ef4444',
                                color: '#fca5a5',
                                borderRadius: '6px',
                                padding: '8px',
                                fontSize: '12px',
                                fontWeight: '600',
                                cursor: actionLoading[submission.id] ? 'not-allowed' : 'pointer',
                                transition: 'all 0.2s',
                                opacity: actionLoading[submission.id] ? 0.5 : 1,
                              }}
                            >
                              {actionLoading[submission.id] ? 'Processing...' : '✗ Confirm AI'}
                            </motion.button>
                          </>
                        )}
                        {(submission.status === 'approved' || submission.status === 'confirmed_ai') && (
                          <div
                            style={{
                              flex: 1,
                              padding: '8px',
                              textAlign: 'center',
                              fontSize: '12px',
                              fontWeight: '600',
                              color: submission.status === 'approved' ? '#6ee7b7' : '#fca5a5',
                            }}
                          >
                            {submission.status === 'approved' ? '✓ Approved' : '✗ Confirmed AI'}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
};

const ScoreBox = ({ label, score }) => {
  const percentage = Math.round(score * 100);
  const getColor = (s) => {
    if (s < 0.4) return '#10b981';
    if (s < 0.7) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div
      style={{
        background: 'rgba(255, 255, 255, 0.05)',
        border: `1px solid ${getColor(score)}`,
        borderRadius: '6px',
        padding: '8px',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>{label}</div>
      <div style={{ fontSize: '14px', fontWeight: '700', color: getColor(score) }}>
        {percentage}%
      </div>
    </div>
  );
};

export default FlaggedSubmissionsTab;
