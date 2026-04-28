/**
 * TreeGeneratorPanel
 * Slide-in panel for generating custom AI skill trees directly from SkillTreePage.
 */

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X, Sparkles, Loader2, AlertCircle, CheckCircle,
  RefreshCw, ChevronRight, Clock,
} from 'lucide-react';
import api from '../../api/api';

const SUGGESTIONS = [
  'Machine Learning', 'DevOps', 'Web3', 'System Design',
  'Game Dev', 'Data Engineering', 'Cybersecurity', 'Mobile Dev',
  'Kubernetes', 'Rust', 'GraphQL', 'Blockchain',
];

const STATUS_MESSAGES = [
  'Analyzing topic structure...',
  'Identifying prerequisite skills...',
  'Designing learning progression...',
  'Writing quest descriptions...',
  'Finalizing your tree ✦',
];

function StatusCycler() {
  const [idx, setIdx] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setIdx(i => (i + 1) % STATUS_MESSAGES.length), 2000);
    return () => clearInterval(t);
  }, []);
  return (
    <AnimatePresence mode="wait">
      <motion.p
        key={idx}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -6 }}
        className="text-sm text-slate-300 text-center"
      >
        {STATUS_MESSAGES[idx]}
      </motion.p>
    </AnimatePresence>
  );
}

export default function TreeGeneratorPanel({ onClose, onTreeGenerated }) {
  const [topic, setTopic] = useState('');
  const [depth, setDepth] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    setTimeout(() => inputRef.current?.focus(), 150);
  }, []);

  const handleGenerate = async () => {
    if (!topic.trim()) { setError('Enter a topic first'); return; }
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const res = await api.post('/api/skills/generate/', { topic: topic.trim(), depth });
      const treeId = res.data.tree_id;

      // Poll until ready
      for (let i = 0; i < 60; i++) {
        await new Promise(r => setTimeout(r, Math.min(1000 + i * 100, 3000)));
        const detail = await api.get(`/api/skills/generated/${treeId}/`);
        if (detail.data.status === 'ready') {
          setSuccess(detail.data);
          onTreeGenerated?.(detail.data);
          setLoading(false);
          return;
        }
        if (detail.data.status === 'failed') {
          throw new Error('Generation failed. Please try again.');
        }
      }
      throw new Error('Timed out. Please try again.');
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to generate tree.');
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSuccess(null);
    setTopic('');
    setError(null);
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  return (
    <motion.div
      initial={{ x: '100%', opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: '100%', opacity: 0 }}
      transition={{ type: 'spring', damping: 28, stiffness: 280 }}
      className="absolute top-0 right-0 h-full w-[380px] z-30 flex flex-col"
      style={{ background: 'rgba(10,12,16,0.97)', borderLeft: '1px solid rgba(255,255,255,0.07)' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-primary" />
          <span className="font-black text-sm text-white uppercase tracking-wider">AI Tree Generator</span>
        </div>
        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-all">
          <X size={16} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5">
        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center gap-6 py-16">
              <div className="relative">
                <div className="w-16 h-16 rounded-full border-2 border-primary/20 flex items-center justify-center">
                  <Loader2 size={28} className="text-primary animate-spin" />
                </div>
                <div className="absolute inset-0 rounded-full border-2 border-primary/10 animate-ping" />
              </div>
              <StatusCycler />
              <button onClick={() => setLoading(false)} className="text-xs text-slate-500 hover:text-slate-400 transition-colors">
                Cancel
              </button>
            </motion.div>
          ) : success ? (
            <motion.div key="success" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
              <div className="flex items-start gap-3 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
                <CheckCircle size={16} className="mt-0.5 flex-shrink-0" />
                <div className="text-xs leading-relaxed">
                  <span className="font-bold">{success.topic}</span> tree ready —{' '}
                  {success.skills?.length || 0} skills generated.
                </div>
              </div>

              {/* Skills preview */}
              <div className="space-y-2">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Skills Preview</p>
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {success.skills?.map((skill, i) => (
                    <motion.div
                      key={skill.id}
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/5"
                    >
                      <div className="w-2 h-2 rounded-full bg-primary flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold text-white truncate">{skill.title}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <Clock size={10} className="text-slate-500" />
                          <span className="text-[10px] text-slate-500">{skill.estimated_hours || 5}h</span>
                          <div className="flex gap-0.5">
                            {Array.from({ length: 5 }).map((_, j) => (
                              <div key={j} className={`w-1 h-1 rounded-full ${j < (skill.difficulty || 2) ? 'bg-primary' : 'bg-slate-700'}`} />
                            ))}
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              <button
                onClick={handleReset}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-white/10 text-slate-300 text-sm font-semibold hover:bg-white/5 transition-all"
              >
                <RefreshCw size={14} /> Generate Another
              </button>
            </motion.div>
          ) : (
            <motion.div key="form" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-5">
              {/* Topic input */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Topic</label>
                <input
                  ref={inputRef}
                  type="text"
                  value={topic}
                  onChange={e => { setTopic(e.target.value); setError(null); }}
                  onKeyDown={e => e.key === 'Enter' && !loading && handleGenerate()}
                  placeholder="e.g. Machine Learning, DevOps..."
                  className="w-full px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-primary/50 transition-all"
                />
              </div>

              {/* Suggestions */}
              <div className="flex flex-wrap gap-1.5">
                {SUGGESTIONS.map(s => (
                  <button
                    key={s}
                    onClick={() => { setTopic(s); setError(null); }}
                    className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-all ${
                      topic === s
                        ? 'bg-primary/20 border-primary/50 text-primary'
                        : 'bg-white/5 border-white/10 text-slate-400 hover:border-primary/30 hover:text-white'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>

              {/* Depth */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Depth</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { value: 2, label: 'Quick', sub: '2 levels' },
                    { value: 3, label: 'Standard', sub: '3 levels' },
                    { value: 4, label: 'Deep', sub: '4 levels' },
                  ].map(opt => (
                    <button
                      key={opt.value}
                      onClick={() => setDepth(opt.value)}
                      className={`p-2.5 rounded-xl border text-center transition-all ${
                        depth === opt.value
                          ? 'border-primary/50 bg-primary/10 text-white'
                          : 'border-white/10 bg-white/5 text-slate-400 hover:border-white/20'
                      }`}
                    >
                      <div className="text-xs font-bold">{opt.label}</div>
                      <div className="text-[10px] text-slate-500 mt-0.5">{opt.sub}</div>
                    </button>
                  ))}
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs">
                  <AlertCircle size={14} className="flex-shrink-0" />
                  {error}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer CTA */}
      {!loading && !success && (
        <div className="px-5 py-4 border-t border-white/5">
          <button
            onClick={handleGenerate}
            disabled={!topic.trim()}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-bold text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-[0_0_24px_rgba(99,102,241,0.4)] transition-all"
          >
            <Sparkles size={15} />
            Generate Tree
            <ChevronRight size={15} />
          </button>
        </div>
      )}
    </motion.div>
  );
}
