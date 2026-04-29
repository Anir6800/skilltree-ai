import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, CheckCircle2, Circle, Loader2, Sparkles, Zap } from 'lucide-react';
import api from '../api/api';
import MainLayout from '../components/layout/MainLayout';
import ResultModal from '../components/ResultModal';
import useSkillStore from '../store/skillStore';
import useQuestStore from '../store/questStore';
import { cn } from '../utils/cn';

function parseOptions(description = '') {
  const lines = description.split('\n').map((line) => line.trim()).filter(Boolean);
  const optionLines = lines
    .map((line) => {
      const match = line.match(/^([A-Da-d])[\).]\s*(.+)$/);
      return match ? { value: match[1].toUpperCase(), label: match[2] } : null;
    })
    .filter(Boolean);
  return optionLines.length ? optionLines : ['A', 'B', 'C', 'D'].map((value) => ({ value, label: `Option ${value}` }));
}

function MCQQuestPage() {
  const { questId } = useParams();
  const navigate = useNavigate();
  const { fetchSkillTree, fetchSkills } = useSkillStore();
  const { fetchCompletedQuests, fetchQuests } = useQuestStore();

  const [quest, setQuest] = useState(null);
  const [selected, setSelected] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [resultModal, setResultModal] = useState({ open: false, submission: null });

  useEffect(() => {
    let alive = true;
    setLoading(true);
    api.get(`/api/quests/${questId}/`)
      .then((res) => {
        if (!alive) return;
        if (res.data.type !== 'mcq') {
          navigate(`/editor/${questId}`, { replace: true });
          return;
        }
        setQuest(res.data);
      })
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load MCQ quest.'))
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [questId, navigate]);

  const options = useMemo(() => parseOptions(quest?.description), [quest]);

  const handleSubmit = async () => {
    if (!selected || submitting || quest?.is_locked) return;
    setSubmitting(true);
    setError('');
    try {
      const res = await api.post(`/api/quests/${questId}/submit/`, { answer: selected });
      const data = res.data;
      const meta = data.execution_result || {};

      if (data.status === 'passed') {
        await Promise.allSettled([fetchSkillTree(), fetchSkills(), fetchCompletedQuests(), fetchQuests()]);
        (meta.new_badges || []).forEach((badge) => {
          window.dispatchEvent(new CustomEvent('badgeEarned', {
            detail: { ...badge, xp_awarded: meta.xp_awarded || 0 },
          }));
        });
      }

      setResultModal({
        open: true,
        submission: {
          ...data,
          status: data.status,
          quest: data.quest || quest,
          execution_result: meta,
        },
        xpAwarded: meta.xp_awarded || 0,
        unlockedStages: meta.unlocked_skills || [],
      });
    } catch (err) {
      setError(err.response?.data?.message || err.response?.data?.error || 'Unable to submit answer.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <div className="min-h-screen bg-[#0a0c10] flex items-center justify-center">
          <Loader2 className="text-primary animate-spin" size={32} />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="min-h-screen bg-[#0a0c10] text-white p-6 pb-28">
        <div className="max-w-4xl mx-auto space-y-6">
          <button
            onClick={() => navigate('/quests')}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10"
          >
            <ArrowLeft size={16} /> Quests
          </button>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel rounded-3xl border border-primary/20 p-8 shadow-[0_0_60px_rgba(99,102,241,0.18)]"
          >
            <div className="flex items-start justify-between gap-4 mb-6">
              <div>
                <div className="flex items-center gap-2 text-primary text-xs font-black uppercase tracking-widest mb-2">
                  <Sparkles size={14} /> MCQ Quest
                </div>
                <h1 className="text-3xl font-black tracking-tight">{quest?.title}</h1>
                <p className="text-slate-400 mt-2">{quest?.skill_name}</p>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 font-black">
                <Zap size={16} /> {quest?.xp_reward} XP
              </div>
            </div>

            <p className="text-slate-300 leading-relaxed whitespace-pre-wrap mb-8">{quest?.description}</p>

            <div className="grid gap-3">
              {options.map((option) => {
                const active = selected === option.value;
                return (
                  <button
                    key={option.value}
                    onClick={() => setSelected(option.value)}
                    className={cn(
                      'w-full text-left rounded-2xl border p-4 transition-all duration-200 flex items-center gap-3',
                      active
                        ? 'bg-primary/20 border-primary/50 shadow-[0_0_24px_rgba(99,102,241,0.25)]'
                        : 'bg-white/5 border-white/10 hover:bg-white/10'
                    )}
                  >
                    {active ? <CheckCircle2 className="text-primary" /> : <Circle className="text-slate-500" />}
                    <span className="font-black text-white">{option.value}</span>
                    <span className="text-slate-300">{option.label}</span>
                  </button>
                );
              })}
            </div>

            <AnimatePresence>
              {error && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="mt-5 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-300">
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            <button
              onClick={handleSubmit}
              disabled={!selected || submitting || quest?.is_locked}
              className={cn(
                'mt-8 w-full py-4 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-black uppercase tracking-widest text-xs transition-all',
                (!selected || submitting || quest?.is_locked) && 'opacity-40 cursor-not-allowed'
              )}
            >
              {submitting ? 'Evaluating...' : 'Submit Answer'}
            </button>
          </motion.div>
        </div>
      </div>

      <ResultModal
        isOpen={resultModal.open}
        submission={resultModal.submission}
        quote={resultModal.submission?.status === 'passed' ? 'Correct. Progression updated.' : 'Review the concept and try again.'}
        xpAwarded={resultModal.xpAwarded || 0}
        unlockedStages={resultModal.unlockedStages || []}
        onTryAgain={() => setResultModal({ open: false, submission: null })}
        onNextQuest={() => navigate('/skills')}
        onClose={() => setResultModal({ open: false, submission: null })}
      />
    </MainLayout>
  );
}

export default MCQQuestPage;
