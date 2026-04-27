import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';

const AIDetectionBadge = ({ detectionScore, detectionLog, onExplainClick }) => {
  const [expandedLayers, setExpandedLayers] = useState(false);

  if (!detectionScore || detectionScore === 0) {
    return null;
  }

  // Determine risk level
  const getRiskLevel = (score) => {
    if (score < 0.4) return { label: 'Low Risk', color: '#10b981', bgColor: 'rgba(16, 185, 129, 0.1)' };
    if (score < 0.7) return { label: 'Medium Risk', color: '#f59e0b', bgColor: 'rgba(245, 158, 11, 0.1)' };
    return { label: 'High Risk — Please Explain', color: '#ef4444', bgColor: 'rgba(239, 68, 68, 0.1)' };
  };

  const riskLevel = getRiskLevel(detectionScore);
  const percentage = Math.round(detectionScore * 100);

  // Gradient colors for confidence meter
  const getGradientColor = (score) => {
    if (score < 0.4) return 'linear-gradient(90deg, #10b981 0%, #34d399 100%)';
    if (score < 0.7) return 'linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%)';
    return 'linear-gradient(90deg, #ef4444 0%, #f87171 100%)';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      style={{
        background: riskLevel.bgColor,
        border: `1px solid ${riskLevel.color}`,
        borderRadius: '12px',
        padding: '16px',
        marginBottom: '16px',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
        <AlertTriangle size={20} color={riskLevel.color} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '14px', fontWeight: '600', color: riskLevel.color }}>
            {riskLevel.label}
          </div>
          <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '2px' }}>
            AI Assistance Detection Score
          </div>
        </div>
        {detectionScore > 0.7 && (
          <motion.button
            onClick={onExplainClick}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            style={{
              background: riskLevel.color,
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 12px',
              fontSize: '12px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            Explain
          </motion.button>
        )}
      </div>

      {/* Confidence Meter */}
      <div style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
          <span style={{ fontSize: '12px', color: '#d1d5db' }}>Confidence</span>
          <span style={{ fontSize: '12px', fontWeight: '600', color: riskLevel.color }}>
            {percentage}%
          </span>
        </div>
        <div
          style={{
            width: '100%',
            height: '6px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '3px',
            overflow: 'hidden',
          }}
        >
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            style={{
              height: '100%',
              background: getGradientColor(detectionScore),
            }}
          />
        </div>
      </div>

      {/* Layer Breakdown */}
      <motion.button
        onClick={() => setExpandedLayers(!expandedLayers)}
        style={{
          width: '100%',
          background: 'transparent',
          border: 'none',
          color: '#9ca3af',
          fontSize: '12px',
          fontWeight: '500',
          padding: '8px 0',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          transition: 'color 0.2s',
        }}
        onMouseEnter={(e) => (e.target.style.color = '#d1d5db')}
        onMouseLeave={(e) => (e.target.style.color = '#9ca3af')}
      >
        <span>Detection Layers</span>
        {expandedLayers ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </motion.button>

      <AnimatePresence>
        {expandedLayers && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}
          >
            {/* Embedding Layer */}
            <LayerRow
              label="Embedding Similarity"
              score={detectionLog?.embedding_score || 0}
              weight="35%"
            />

            {/* LLM Layer */}
            <LayerRow
              label="LLM Classification"
              score={detectionLog?.llm_score || 0}
              weight="45%"
            />

            {/* Heuristic Layer */}
            <LayerRow
              label="Heuristic Scoring"
              score={detectionLog?.heuristic_score || 0}
              weight="20%"
            />

            {/* LLM Reasoning */}
            {detectionLog?.llm_reasoning && (
              <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '6px', fontWeight: '500' }}>
                  LLM Analysis
                </div>
                <div style={{ fontSize: '12px', color: '#d1d5db', lineHeight: '1.5' }}>
                  {detectionLog.llm_reasoning.reasoning || 'No reasoning provided'}
                </div>
                {detectionLog.llm_reasoning.key_signals && detectionLog.llm_reasoning.key_signals.length > 0 && (
                  <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {detectionLog.llm_reasoning.key_signals.slice(0, 3).map((signal, idx) => (
                      <span
                        key={idx}
                        style={{
                          fontSize: '11px',
                          background: 'rgba(239, 68, 68, 0.2)',
                          color: '#fca5a5',
                          padding: '4px 8px',
                          borderRadius: '4px',
                        }}
                      >
                        {signal}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

const LayerRow = ({ label, score, weight }) => {
  const percentage = Math.round(score * 100);

  return (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
        <span style={{ fontSize: '11px', color: '#9ca3af' }}>
          {label} <span style={{ color: '#6b7280' }}>({weight})</span>
        </span>
        <span style={{ fontSize: '11px', fontWeight: '600', color: '#d1d5db' }}>
          {percentage}%
        </span>
      </div>
      <div
        style={{
          width: '100%',
          height: '4px',
          background: 'rgba(255, 255, 255, 0.05)',
          borderRadius: '2px',
          overflow: 'hidden',
        }}
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          style={{
            height: '100%',
            background: 'linear-gradient(90deg, #7c6af5 0%, #a78bfa 100%)',
          }}
        />
      </div>
    </div>
  );
};

export default AIDetectionBadge;
