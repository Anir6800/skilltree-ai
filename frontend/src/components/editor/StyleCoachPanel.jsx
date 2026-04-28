import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, CheckCircle2, AlertCircle, Zap } from 'lucide-react';
import api from '../../api/api';

const StyleCoachPanel = ({ submission, isOpen }) => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedIssues, setExpandedIssues] = useState({});

  useEffect(() => {
    if (isOpen && submission?.id && submission?.status === 'passed') {
      fetchStyleReport();
    }
  }, [isOpen, submission?.id]);

  const fetchStyleReport = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get(`/api/style/submissions/${submission.id}/report/`);
      setReport(response.data);
    } catch (err) {
      if (err.response?.status === 404) {
        generateStyleReport();
      } else {
        setError('Failed to load style report');
      }
    } finally {
      setLoading(false);
    }
  };

  const generateStyleReport = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post(`/api/style/submissions/${submission.id}/analyze/`, {
        code: submission.code,
        language: submission.language
      });
      setReport(response.data);
    } catch (err) {
      if (err.response?.status === 503) {
        setError('Style analysis service is currently unavailable');
      } else {
        setError(err.response?.data?.error || 'Failed to generate style report');
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleIssue = (index) => {
    setExpandedIssues(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const getReadabilityColor = (score) => {
    if (score >= 8) return '#10b981';
    if (score >= 6) return '#f59e0b';
    return '#ef4444';
  };

  if (!isOpen) return null;

  if (!submission || submission.status !== 'passed') {
    return (
      <div style={{
        padding: '20px',
        background: 'rgba(15, 18, 25, 0.6)',
        borderRadius: '12px',
        color: '#9ca3af',
        textAlign: 'center'
      }}>
        <p>Style analysis is only available for passed submissions.</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      style={{
        background: 'rgba(15, 18, 25, 0.6)',
        borderRadius: '12px',
        padding: '20px',
        backdropFilter: 'blur(20px)'
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{
          fontSize: '16px',
          fontWeight: '600',
          color: '#fff',
          marginBottom: '4px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <Zap size={18} style={{ color: '#7c6af5' }} />
          Style Report
        </h3>
        <p style={{ fontSize: '13px', color: '#9ca3af' }}>
          Your code works. Now make it beautiful.
        </p>
      </div>

      {/* Loading State */}
      {loading && (
        <div style={{
          textAlign: 'center',
          padding: '20px',
          color: '#9ca3af'
        }}>
          <div style={{
            display: 'inline-block',
            width: '20px',
            height: '20px',
            border: '2px solid rgba(124, 106, 245, 0.3)',
            borderTop: '2px solid #7c6af5',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
          <p style={{ marginTop: '12px' }}>Analyzing code style...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '8px',
          padding: '12px',
          color: '#fca5a5',
          fontSize: '13px'
        }}>
          {error}
        </div>
      )}

      {/* Report Content */}
      {report && !loading && (
        <>
          {/* Readability Score */}
          <div style={{ marginBottom: '20px' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '8px'
            }}>
              <label style={{ fontSize: '13px', fontWeight: '600', color: '#d1d5db' }}>
                Readability Score
              </label>
              <span style={{
                fontSize: '18px',
                fontWeight: '700',
                color: getReadabilityColor(report.readability_score)
              }}>
                {report.readability_score}/10
              </span>
            </div>
            <div style={{
              width: '100%',
              height: '8px',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${(report.readability_score / 10) * 100}%`,
                height: '100%',
                background: `linear-gradient(90deg, ${getReadabilityColor(report.readability_score)} 0%, ${getReadabilityColor(report.readability_score)}dd 100%)`,
                transition: 'width 0.3s ease'
              }} />
            </div>
          </div>

          {/* Naming Quality */}
          {report.naming_quality && (
            <div style={{
              background: 'rgba(124, 106, 245, 0.1)',
              border: '1px solid rgba(124, 106, 245, 0.2)',
              borderRadius: '8px',
              padding: '12px',
              marginBottom: '16px',
              fontSize: '13px',
              color: '#d1d5db',
              lineHeight: '1.5'
            }}>
              <div style={{ fontWeight: '600', color: '#7c6af5', marginBottom: '4px' }}>
                Naming Quality
              </div>
              {report.naming_quality}
            </div>
          )}

          {/* Idiomatic Patterns */}
          {report.idiomatic_patterns && (
            <div style={{
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.2)',
              borderRadius: '8px',
              padding: '12px',
              marginBottom: '16px',
              fontSize: '13px',
              color: '#d1d5db',
              lineHeight: '1.5'
            }}>
              <div style={{ fontWeight: '600', color: '#10b981', marginBottom: '4px' }}>
                Idiomatic Patterns
              </div>
              {report.idiomatic_patterns}
            </div>
          )}

          {/* Positive Patterns */}
          {report.positive_patterns && report.positive_patterns.length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <h4 style={{
                fontSize: '13px',
                fontWeight: '600',
                color: '#10b981',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <CheckCircle2 size={16} />
                Positive Patterns
              </h4>
              <div style={{ display: 'grid', gap: '6px' }}>
                {report.positive_patterns.map((pattern, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: 'rgba(16, 185, 129, 0.1)',
                      border: '1px solid rgba(16, 185, 129, 0.2)',
                      borderRadius: '6px',
                      padding: '8px 12px',
                      fontSize: '12px',
                      color: '#d1d5db',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}
                  >
                    <div style={{
                      width: '4px',
                      height: '4px',
                      borderRadius: '50%',
                      background: '#10b981',
                      flexShrink: 0
                    }} />
                    {pattern}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Style Issues */}
          {report.style_issues && report.style_issues.length > 0 && (
            <div>
              <h4 style={{
                fontSize: '13px',
                fontWeight: '600',
                color: '#f59e0b',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <AlertCircle size={16} />
                Style Issues ({report.style_issues.length})
              </h4>
              <div style={{ display: 'grid', gap: '8px' }}>
                {report.style_issues.map((issue, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    style={{
                      background: 'rgba(245, 158, 11, 0.1)',
                      border: '1px solid rgba(245, 158, 11, 0.2)',
                      borderRadius: '8px',
                      overflow: 'hidden'
                    }}
                  >
                    <button
                      onClick={() => toggleIssue(idx)}
                      style={{
                        width: '100%',
                        padding: '12px',
                        background: 'transparent',
                        border: 'none',
                        color: '#d1d5db',
                        textAlign: 'left',
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        fontSize: '13px',
                        fontWeight: '500'
                      }}
                    >
                      <div>
                        <div style={{ color: '#f59e0b', marginBottom: '2px' }}>
                          {issue.issue}
                        </div>
                        <div style={{ fontSize: '11px', color: '#9ca3af' }}>
                          {issue.line_hint}
                        </div>
                      </div>
                      {expandedIssues[idx] ? (
                        <ChevronUp size={16} style={{ flexShrink: 0 }} />
                      ) : (
                        <ChevronDown size={16} style={{ flexShrink: 0 }} />
                      )}
                    </button>

                    <AnimatePresence>
                      {expandedIssues[idx] && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          style={{
                            borderTop: '1px solid rgba(245, 158, 11, 0.2)',
                            padding: '12px',
                            background: 'rgba(0, 0, 0, 0.2)'
                          }}
                        >
                          <div style={{ marginBottom: '12px' }}>
                            <div style={{
                              fontSize: '11px',
                              fontWeight: '600',
                              color: '#9ca3af',
                              marginBottom: '4px',
                              textTransform: 'uppercase'
                            }}>
                              Suggestion
                            </div>
                            <div style={{
                              fontSize: '12px',
                              color: '#d1d5db',
                              lineHeight: '1.5'
                            }}>
                              {issue.suggestion}
                            </div>
                          </div>

                          {issue.example_fix && (
                            <div>
                              <div style={{
                                fontSize: '11px',
                                fontWeight: '600',
                                color: '#9ca3af',
                                marginBottom: '4px',
                                textTransform: 'uppercase'
                              }}>
                                Example Fix
                              </div>
                              <div style={{
                                background: 'rgba(0, 0, 0, 0.3)',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                borderRadius: '6px',
                                padding: '8px',
                                fontSize: '11px',
                                fontFamily: 'monospace',
                                color: '#10b981',
                                overflow: 'auto',
                                maxHeight: '150px',
                                lineHeight: '1.4'
                              }}>
                                {issue.example_fix}
                              </div>
                            </div>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* No Issues */}
          {(!report.style_issues || report.style_issues.length === 0) && (
            <div style={{
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.2)',
              borderRadius: '8px',
              padding: '16px',
              textAlign: 'center',
              color: '#10b981'
            }}>
              <CheckCircle2 size={24} style={{ margin: '0 auto 8px' }} />
              <p style={{ fontSize: '13px', fontWeight: '600' }}>
                No style issues found!
              </p>
              <p style={{ fontSize: '12px', color: '#6ee7b7', marginTop: '4px' }}>
                Your code follows best practices.
              </p>
            </div>
          )}
        </>
      )}

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </motion.div>
  );
};

export default StyleCoachPanel;
