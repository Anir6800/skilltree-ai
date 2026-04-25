1/**
 * SkillTree AI - Editor Page
 * Full-featured code editor with Monaco, quest context, AI feedback, and submission polling.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Editor from '@monaco-editor/react';
import api from '../api/api';
import {
  Play, Send, RotateCcw, ChevronDown, ChevronUp, ChevronLeft,
  Bot, Zap, Clock, CheckCircle2, XCircle, AlertCircle,
  Loader2, Terminal, Sparkles, ThumbsUp, ThumbsDown, Lightbulb,
  Copy, Check, Code2,
} from 'lucide-react';
import BottomNav from '../components/layout/BottomNav';
import useEditorStore, { DEFAULT_TEMPLATES } from '../store/editorStore';
import { cn } from '../utils/cn';

// ─── Constants ────────────────────────────────────────────────────────────────

const LANGUAGES = [
  { id: 'python',     label: 'Python',     monacoId: 'python'     },
  { id: 'javascript', label: 'JavaScript', monacoId: 'javascript' },
  { id: 'cpp',        label: 'C++',        monacoId: 'cpp'        },
  { id: 'java',       label: 'Java',       monacoId: 'java'       },
  { id: 'go',         label: 'Go',         monacoId: 'go'         },
];

const LANG_COLORS = {
  python:     { bg: 'bg-blue-500/20',   border: 'border-blue-500/40',   text: 'text-blue-400'   },
  javascript: { bg: 'bg-yellow-500/20', border: 'border-yellow-500/40', text: 'text-yellow-400' },
  cpp:        { bg: 'bg-cyan-500/20',   border: 'border-cyan-500/40',   text: 'text-cyan-400'   },
  java:       { bg: 'bg-orange-500/20', border: 'border-orange-500/40', text: 'text-orange-400' },
  go:         { bg: 'bg-teal-500/20',   border: 'border-teal-500/40',   text: 'text-teal-400'   },
};

const POLL_INTERVAL_MS = 2000;
const MAX_POLL_ATTEMPTS = 30;

// ─── Monaco Theme ─────────────────────────────────────────────────────────────

function defineMonacoTheme(monaco) {
  monaco.editor.defineTheme('skilltree-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'keyword',         foreground: '7c6af5', fontStyle: 'bold' },
      { token: 'keyword.control', foreground: 'a78bfa' },
      { token: 'string',          foreground: '3dd68c' },
      { token: 'comment',         foreground: '4b5563', fontStyle: 'italic' },
      { token: 'number',          foreground: 'f59e0b' },
      { token: 'type',            foreground: '38bdf8' },
      { token: 'function',        foreground: 'c084fc' },
      { token: 'variable',        foreground: 'e2e8f0' },
      { token: 'operator',        foreground: 'f43f5e' },
      { token: 'delimiter',       foreground: '94a3b8' },
    ],
    colors: {
      'editor.background':                    '#0a0c10',
      'editor.foreground':                    '#e2e8f0',
      'editor.lineHighlightBackground':       '#ffffff08',
      'editor.selectionBackground':           '#6366f130',
      'editor.inactiveSelectionBackground':   '#6366f118',
      'editorLineNumber.foreground':          '#374151',
      'editorLineNumber.activeForeground':    '#6366f1',
      'editorCursor.foreground':              '#6366f1',
      'editorIndentGuide.background1':        '#1f2937',
      'editorIndentGuide.activeBackground1':  '#374151',
      'editorBracketMatch.background':        '#6366f120',
      'editorBracketMatch.border':            '#6366f1',
      'scrollbarSlider.background':           '#ffffff10',
      'scrollbarSlider.hoverBackground':      '#ffffff20',
      'editorWidget.background':              '#0f172a',
      'editorSuggestWidget.background':       '#0f172a',
      'editorSuggestWidget.border':           '#ffffff10',
      'editorSuggestWidget.selectedBackground': '#6366f120',
    },
  });
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function DifficultyPips({ level }) {
  const filled = Math.min(5, Math.max(1, Math.round(level)));
  return (
    <div className="flex items-center gap-1">
      {[...Array(5)].map((_, i) => (
        <div key={i} className={cn(
          'w-1.5 h-1.5 rounded-full transition-all duration-300',
          i < filled ? 'bg-primary shadow-[0_0_6px_rgba(99,102,241,0.8)]' : 'bg-white/10'
        )} />
      ))}
    </div>
  );
}

function StatusBanner({ execStatus }) {
  const configs = {
    running: { text: 'RUNNING',           icon: Loader2,      spin: true,  cls: 'bg-primary/10 border-primary/30 text-primary' },
    passed:  { text: 'ALL TESTS PASSED',  icon: CheckCircle2, spin: false, cls: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' },
    failed:  { text: 'TESTS FAILED',      icon: XCircle,      spin: false, cls: 'bg-red-500/10 border-red-500/30 text-red-400' },
    error:   { text: 'EXECUTION ERROR',   icon: AlertCircle,  spin: false, cls: 'bg-red-500/10 border-red-500/30 text-red-400' },
    timeout: { text: 'TIMED OUT',         icon: Clock,        spin: false, cls: 'bg-amber-500/10 border-amber-500/30 text-amber-400' },
  };
  const cfg = configs[execStatus];
  if (!cfg) return null;
  const Icon = cfg.icon;
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className={cn('flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-bold uppercase tracking-widest', cfg.cls)}
    >
      <Icon size={13} className={cfg.spin ? 'animate-spin' : ''} />
      {cfg.text}
    </motion.div>
  );
}

function TestCaseRow({ tc, index }) {
  return (
    <motion.tr
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.04 }}
      className={cn(
        'border-b border-white/5',
        tc.status === 'passed' && 'bg-emerald-500/5',
        tc.status === 'failed' && 'bg-red-500/5',
      )}
    >
      <td className="px-3 py-2.5 font-mono text-xs text-slate-300 max-w-[100px] truncate">{tc.input ?? '—'}</td>
      <td className="px-3 py-2.5 font-mono text-xs text-slate-300 max-w-[100px] truncate">{tc.expected ?? '—'}</td>
      <td className="px-3 py-2.5 font-mono text-xs text-slate-300 max-w-[100px] truncate">{tc.actual ?? '—'}</td>
      <td className="px-3 py-2.5">
        {tc.status === 'passed' && <span className="flex items-center gap-1 text-emerald-400 text-xs font-bold"><CheckCircle2 size={12} />Pass</span>}
        {tc.status === 'failed' && <span className="flex items-center gap-1 text-red-400 text-xs font-bold"><XCircle size={12} />Fail</span>}
        {!tc.status && <span className="text-slate-600 text-xs">—</span>}
      </td>
    </motion.tr>
  );
}

function AiFeedbackPanel({ feedback, detectionScore }) {
  const [open, setOpen] = useState(true);
  if (!feedback && detectionScore === undefined) return null;
  const score = feedback?.score ?? 0;
  const scoreColor = score >= 80 ? 'text-emerald-400' : score >= 50 ? 'text-amber-400' : 'text-red-400';
  const risk = detectionScore >= 0.7
    ? { label: 'High Risk',   color: 'text-red-400',     bg: 'bg-red-500/10 border-red-500/30' }
    : detectionScore >= 0.4
    ? { label: 'Medium Risk', color: 'text-amber-400',   bg: 'bg-amber-500/10 border-amber-500/30' }
    : { label: 'Low Risk',    color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30' };

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-panel rounded-2xl overflow-hidden">
      <button onClick={() => setOpen(v => !v)} className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/5 transition-colors">
        <div className="flex items-center gap-2">
          <Sparkles size={14} className="text-primary drop-shadow-[0_0_8px_rgba(99,102,241,0.8)]" />
          <span className="text-xs font-bold uppercase tracking-widest text-slate-300">AI Feedback</span>
        </div>
        {open ? <ChevronUp size={13} className="text-slate-500" /> : <ChevronDown size={13} className="text-slate-500" />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} className="overflow-hidden">
            <div className="px-4 pb-4 space-y-3 border-t border-white/5">
              <div className="flex gap-2 pt-3">
                {feedback?.score !== undefined && (
                  <div className="flex-1 glass-card rounded-xl p-3 text-center">
                    <div className={cn('text-xl font-black', scoreColor)}>{score}</div>
                    <div className="text-[9px] font-bold uppercase tracking-widest text-slate-500 mt-0.5">Quality</div>
                  </div>
                )}
                {detectionScore !== undefined && (
                  <div className={cn('flex-1 rounded-xl p-3 text-center border', risk.bg)}>
                    <div className={cn('text-xl font-black', risk.color)}>{Math.round(detectionScore * 100)}%</div>
                    <div className={cn('text-[9px] font-bold uppercase tracking-widest mt-0.5', risk.color)}>{risk.label}</div>
                  </div>
                )}
              </div>
              {feedback?.pros?.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-1.5"><ThumbsUp size={11} className="text-emerald-400" /><span className="text-[9px] font-bold uppercase tracking-widest text-slate-500">Strengths</span></div>
                  {feedback.pros.map((p, i) => <div key={i} className="flex items-start gap-1.5 text-xs text-slate-300 mb-1"><CheckCircle2 size={10} className="text-emerald-400 mt-0.5 shrink-0" />{p}</div>)}
                </div>
              )}
              {feedback?.cons?.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-1.5"><ThumbsDown size={11} className="text-red-400" /><span className="text-[9px] font-bold uppercase tracking-widest text-slate-500">Weaknesses</span></div>
                  {feedback.cons.map((c, i) => <div key={i} className="flex items-start gap-1.5 text-xs text-slate-300 mb-1"><XCircle size={10} className="text-red-400 mt-0.5 shrink-0" />{c}</div>)}
                </div>
              )}
              {feedback?.suggestions?.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-1.5"><Lightbulb size={11} className="text-amber-400" /><span className="text-[9px] font-bold uppercase tracking-widest text-slate-500">Suggestions</span></div>
                  {feedback.suggestions.map((s, i) => <div key={i} className="flex items-start gap-1.5 text-xs text-slate-300 mb-1"><span className="text-amber-400 shrink-0">→</span>{s}</div>)}
                </div>
              )}
              {feedback?.summary && <p className="text-xs text-slate-400 italic border-t border-white/5 pt-2">{feedback.summary}</p>}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

function EditorPage() {
  const { questId } = useParams();
  const navigate = useNavigate();

  const { getQuestCode, getQuestLanguage, setQuestCode, setQuestLanguage, resetQuestCode, aiModeEnabled, toggleAiMode } = useEditorStore();

  const [quest, setQuest] = useState(null);
  const [questLoading, setQuestLoading] = useState(true);
  const [questError, setQuestError] = useState(null);
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);
  const [questPanelOpen, setQuestPanelOpen] = useState(true);
  const [copied, setCopied] = useState(false);
  const [execStatus, setExecStatus] = useState('idle');
  const [execOutput, setExecOutput] = useState(null);
  const [aiFeedback, setAiFeedback] = useState(null);
  const [detectionScore, setDetectionScore] = useState(undefined);
  const [execTime, setExecTime] = useState(null);

  const editorRef = useRef(null);
  const pollRef = useRef(null);
  const pollAttemptsRef = useRef(0);
  const langDropdownRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => { if (langDropdownRef.current && !langDropdownRef.current.contains(e.target)) setLangDropdownOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Load quest
  useEffect(() => {
    if (!questId) return;
    setQuestLoading(true);
    setQuestError(null);
    api.get(`/api/quests/${questId}/`)
      .then((res) => {
        const q = res.data;
        setQuest(q);
        const savedLang = getQuestLanguage(questId);
        const lang = savedLang || 'python';
        setLanguage(lang);
        setCode(getQuestCode(questId, q.starter_code, lang));
      })
      .catch((err) => setQuestError(err.response?.data?.detail || 'Failed to load quest.'))
      .finally(() => setQuestLoading(false));
  }, [questId]);

  const handleCodeChange = useCallback((val) => {
    const v = val ?? '';
    setCode(v);
    if (questId) setQuestCode(questId, v);
  }, [questId, setQuestCode]);

  const handleLanguageChange = useCallback((newLang) => {
    setLanguage(newLang);
    setLangDropdownOpen(false);
    if (questId) {
      setQuestLanguage(questId, newLang);
      const currentDefault = DEFAULT_TEMPLATES[language] || '';
      if (!code || code === currentDefault) {
        const newCode = quest?.starter_code || DEFAULT_TEMPLATES[newLang] || '';
        setCode(newCode);
        setQuestCode(questId, newCode);
      }
    }
  }, [questId, language, code, quest, setQuestLanguage, setQuestCode]);

  const clearPoll = useCallback(() => {
    if (pollRef.current) { clearTimeout(pollRef.current); pollRef.current = null; }
    pollAttemptsRef.current = 0;
  }, []);

  useEffect(() => () => clearPoll(), [clearPoll]);

  const pollStatus = useCallback((sid) => {
    if (pollAttemptsRef.current >= MAX_POLL_ATTEMPTS) { setExecStatus('timeout'); clearPoll(); return; }
    pollAttemptsRef.current += 1;
    pollRef.current = setTimeout(async () => {
      try {
        const res = await api.get(`/api/execute/status/${sid}/`);
        const data = res.data;
        if (data.status === 'pending' || data.status === 'running') { pollStatus(sid); return; }
        clearPoll();
        const result = data.execution_result || {};
        const tests = result.test_results || [];
        setExecTime(result.time_ms ?? null);
        setExecOutput({ stdout: result.output || result.stdout || '', stderr: result.stderr || '', test_results: tests });
        const allPassed = tests.length > 0 && tests.every(t => t.status === 'passed');
        setExecStatus(data.status === 'passed' || allPassed ? 'passed' : data.status === 'failed' ? 'failed' : 'error');
        if (data.ai_feedback && Object.keys(data.ai_feedback).length > 0) setAiFeedback(data.ai_feedback);
        if (data.ai_detection_score !== undefined) setDetectionScore(data.ai_detection_score);
      } catch { clearPoll(); setExecStatus('error'); setExecOutput({ stdout: '', stderr: 'Failed to fetch status.', test_results: [] }); }
    }, POLL_INTERVAL_MS);
  }, [clearPoll]);

  const handleRun = useCallback(async () => {
    if (!code.trim() || execStatus === 'running') return;
    clearPoll(); setExecStatus('running'); setExecOutput(null); setAiFeedback(null); setDetectionScore(undefined); setExecTime(null); pollAttemptsRef.current = 0;
    try {
      // If quest has test cases, use test endpoint with AI simulation support
      if (quest?.test_cases && quest.test_cases.length > 0) {
        // Map quest test cases to executor format
        const mappedTestCases = quest.test_cases.map(tc => ({
          input: tc.input || '',
          expected: tc.expected_output || tc.expected || ''
        }));
        
        const res = await api.post('/api/execute/test/', {
          code: code.trim(),
          language,
          test_cases: mappedTestCases,
          use_ai_simulation: aiModeEnabled
        });
        const data = res.data;
        
        // Handle direct response (AI simulation or quick execution)
        setExecTime(data.execution_time_ms ?? 0);
        const tests = data.results || [];
        setExecOutput({
          stdout: data.overall_assessment || '',
          stderr: data.error || '',
          test_results: tests.map(t => ({
            input: t.input,
            expected: t.expected,
            actual: t.actual,
            status: t.passed ? 'passed' : 'failed',
            reasoning: t.reasoning
          })),
          is_simulated: data.is_simulated
        });
        setExecStatus(data.tests_passed === data.tests_total ? 'passed' : 'failed');
        return;
      }
      
      // Fallback to simple execution for quests without test cases
      const res = await api.post('/api/execute/', { code: code.trim(), language, ...(questId && { quest_id: questId }), run_only: true });
      const data = res.data;
      if (data.status && data.status !== 'pending' && data.status !== 'running') {
        const result = data.execution_result || data;
        const tests = result.test_results || [];
        setExecTime(result.time_ms ?? null);
        setExecOutput({ stdout: result.output || result.stdout || data.output || '', stderr: result.stderr || '', test_results: tests });
        setExecStatus(tests.length > 0 && tests.every(t => t.status === 'passed') ? 'passed' : tests.length > 0 ? 'failed' : 'passed');
        return;
      }
      const sid = data.submission_id || data.id || data.task_id;
      if (sid) { pollStatus(sid); } else { setExecOutput({ stdout: data.output || data.stdout || '', stderr: data.stderr || '', test_results: [] }); setExecStatus('passed'); }
    } catch (err) { clearPoll(); setExecStatus('error'); setExecOutput({ stdout: '', stderr: err.response?.data?.error || err.response?.data?.detail || 'Execution failed.', test_results: [] }); }
  }, [code, language, questId, quest, execStatus, aiModeEnabled, clearPoll, pollStatus]);

  const handleSubmit = useCallback(async () => {
    if (!code.trim() || execStatus === 'running' || !questId) return;
    clearPoll(); setExecStatus('running'); setExecOutput(null); setAiFeedback(null); setDetectionScore(undefined); setExecTime(null); pollAttemptsRef.current = 0;
    try {
      const res = await api.post(`/api/quests/${questId}/submit/`, { code: code.trim(), language });
      const data = res.data;
      const sid = data.submission_id || data.id;
      if (sid) { pollStatus(sid); } else { setExecStatus('error'); setExecOutput({ stdout: '', stderr: 'No task ID returned.', test_results: [] }); }
    } catch (err) { clearPoll(); setExecStatus('error'); setExecOutput({ stdout: '', stderr: err.response?.data?.error || err.response?.data?.detail || 'Submission failed.', test_results: [] }); }
  }, [code, language, questId, execStatus, clearPoll, pollStatus]);

  const handleReset = useCallback(() => {
    if (!questId) return;
    const resetCode = resetQuestCode(questId, quest?.starter_code, language);
    setCode(resetCode); setExecStatus('idle'); setExecOutput(null); setAiFeedback(null); setDetectionScore(undefined); setExecTime(null); clearPoll();
  }, [questId, quest, language, resetQuestCode, clearPoll]);

  const handleEditorMount = useCallback((editor, monaco) => {
    editorRef.current = editor;
    defineMonacoTheme(monaco);
    monaco.editor.setTheme('skilltree-dark');
    editor.focus();
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, handleRun);
  }, [handleRun]);

  const handleCopyOutput = useCallback(() => {
    const text = [execOutput?.stdout, execOutput?.stderr].filter(Boolean).join('\n');
    navigator.clipboard.writeText(text).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500); });
  }, [execOutput]);

  const testResults = execOutput?.test_results || [];
  const passedCount = testResults.filter(t => t.status === 'passed').length;
  const isRunning = execStatus === 'running';
  const currentLang = LANGUAGES.find(l => l.id === language) || LANGUAGES[0];
  const langColor = LANG_COLORS[language] || LANG_COLORS.python;

  // ── Loading ──────────────────────────────────────────────────────────────────
  if (questLoading) return (
    <div className="fixed inset-0 bg-[#0a0c10] flex items-center justify-center">
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
      </div>
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="flex flex-col items-center gap-4">
        <Loader2 size={32} className="text-primary animate-spin drop-shadow-[0_0_12px_rgba(99,102,241,0.8)]" />
        <p className="text-slate-400 text-sm font-medium">Loading quest...</p>
      </motion.div>
    </div>
  );

  // ── Error ────────────────────────────────────────────────────────────────────
  if (questError) return (
    <div className="fixed inset-0 bg-[#0a0c10] flex items-center justify-center p-6">
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
      </div>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-8 rounded-3xl max-w-md w-full text-center relative z-10">
        <AlertCircle size={40} className="text-red-400 mx-auto mb-4" />
        <h2 className="text-xl font-black text-white mb-2">Quest Not Found</h2>
        <p className="text-slate-400 text-sm mb-6">{questError}</p>
        <div className="flex gap-3 justify-center">
          <button onClick={() => { setQuestError(null); setQuestLoading(true); api.get(`/api/quests/${questId}/`).then(r => { setQuest(r.data); setQuestLoading(false); }).catch(e => { setQuestError(e.response?.data?.detail || 'Failed.'); setQuestLoading(false); }); }} className="px-5 py-2.5 rounded-xl bg-primary/20 border border-primary/30 text-primary text-sm font-bold hover:bg-primary/30 transition-all duration-200">Retry</button>
          <button onClick={() => navigate('/quests')} className="px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 text-slate-300 text-sm font-bold hover:bg-white/10 transition-all duration-200">Back to Quests</button>
        </div>
      </motion.div>
    </div>
  );

  // ── Main render ──────────────────────────────────────────────────────────────
  return (
    // Fixed full-screen layout — bypasses MainLayout padding entirely
    <div className="fixed inset-0 bg-[#0a0c10] text-white flex flex-col overflow-hidden">

      {/* Ambient glows */}
      <div className="fixed inset-0 pointer-events-none -z-10">
        <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
      </div>

      {/* ── Top Bar ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/5 bg-black/40 backdrop-blur-xl shrink-0 z-30">
        {/* Left */}
        <div className="flex items-center gap-3 min-w-0">
          <button onClick={() => navigate('/quests')} className="p-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-200 shrink-0">
            <ChevronLeft size={15} className="text-slate-400" />
          </button>
          {quest && (
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <Code2 size={13} className="text-primary shrink-0" />
                <h1 className="text-sm font-black text-white truncate">{quest.title}</h1>
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                <DifficultyPips level={quest.difficulty_multiplier} />
                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">{quest.xp_reward} XP</span>
                <span className={cn('text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-md border', langColor.bg, langColor.border, langColor.text)}>{quest.type}</span>
              </div>
            </div>
          )}
        </div>

        {/* Center: status */}
        <div className="hidden md:flex items-center">
          <AnimatePresence mode="wait">
            {execStatus !== 'idle' && <StatusBanner key={execStatus} execStatus={execStatus} />}
          </AnimatePresence>
        </div>

        {/* Right: AI mode */}
        <button
          onClick={toggleAiMode}
          className={cn(
            'flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-bold uppercase tracking-wider transition-all duration-300',
            aiModeEnabled
              ? 'bg-primary/20 border-primary/40 text-primary shadow-[0_0_16px_rgba(99,102,241,0.3)]'
              : 'bg-white/5 border-white/10 text-slate-400 hover:bg-white/10'
          )}
        >
          <Bot size={13} className={aiModeEnabled ? 'drop-shadow-[0_0_6px_rgba(99,102,241,0.8)]' : ''} />
          <span className="hidden sm:inline">AI Mode</span>
          {aiModeEnabled && <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />}
        </button>
      </div>

      {/* ── Two-pane body ────────────────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ══ LEFT — Editor 60% ══ */}
        <div className="flex flex-col border-r border-white/5" style={{ width: '60%' }}>

          {/* Toolbar */}
          <div className="flex items-center gap-2 px-3 py-2 border-b border-white/5 bg-black/20 shrink-0 flex-wrap">

            {/* Language selector — custom glass dropdown */}
            <div className="relative" ref={langDropdownRef}>
              <button
                onClick={() => setLangDropdownOpen(v => !v)}
                className={cn(
                  'flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-bold uppercase tracking-wider transition-all duration-200',
                  langColor.bg, langColor.border, langColor.text,
                  'hover:opacity-90'
                )}
              >
                <span>{currentLang.label}</span>
                <ChevronDown size={11} className={cn('transition-transform duration-200', langDropdownOpen && 'rotate-180')} />
              </button>

              <AnimatePresence>
                {langDropdownOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -6, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -6, scale: 0.97 }}
                    transition={{ duration: 0.15 }}
                    className="absolute top-full left-0 mt-1.5 z-50 glass-panel rounded-xl overflow-hidden border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.5)] min-w-[140px]"
                  >
                    {LANGUAGES.map((lang) => {
                      const lc = LANG_COLORS[lang.id];
                      const isActive = lang.id === language;
                      return (
                        <button
                          key={lang.id}
                          onClick={() => handleLanguageChange(lang.id)}
                          className={cn(
                            'w-full flex items-center gap-2.5 px-4 py-2.5 text-xs font-bold uppercase tracking-wider transition-all duration-150',
                            isActive
                              ? cn(lc.bg, lc.text, 'border-l-2', lc.border.replace('border-', 'border-l-'))
                              : 'text-slate-400 hover:bg-white/5 hover:text-white'
                          )}
                        >
                          <span className={cn('w-1.5 h-1.5 rounded-full', isActive ? lc.text.replace('text-', 'bg-') : 'bg-slate-600')} />
                          {lang.label}
                          {isActive && <CheckCircle2 size={11} className="ml-auto" />}
                        </button>
                      );
                    })}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="w-px h-5 bg-white/10" />

            {/* Run */}
            <button
              onClick={handleRun}
              disabled={isRunning || !code.trim()}
              className={cn(
                'flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-200',
                'bg-emerald-500/20 border border-emerald-500/30 text-emerald-400',
                'hover:bg-emerald-500/30 hover:shadow-[0_0_16px_rgba(52,211,153,0.3)]',
                (isRunning || !code.trim()) && 'opacity-40 cursor-not-allowed'
              )}
            >
              {isRunning ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
              Run
            </button>

            {/* Submit */}
            {questId && (
              <button
                onClick={handleSubmit}
                disabled={isRunning || !code.trim()}
                className={cn(
                  'flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-200',
                  'bg-gradient-to-r from-primary/80 to-accent/80 border border-primary/40 text-white',
                  'hover:from-primary hover:to-accent hover:shadow-[0_0_20px_rgba(99,102,241,0.4)]',
                  (isRunning || !code.trim()) && 'opacity-40 cursor-not-allowed'
                )}
              >
                <Send size={12} />
                Submit
                <span className="text-[9px] opacity-70 font-black">+XP</span>
              </button>
            )}

            {/* Reset */}
            <button
              onClick={handleReset}
              disabled={isRunning}
              className={cn(
                'flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-200',
                'bg-white/5 border border-white/10 text-slate-400 hover:bg-white/10 hover:text-white',
                isRunning && 'opacity-40 cursor-not-allowed'
              )}
            >
              <RotateCcw size={12} />
              Reset
            </button>

            {/* Shortcut hint */}
            <div className="ml-auto flex items-center gap-1 px-2 py-1 rounded-lg bg-white/5 border border-white/5">
              <kbd className="text-[9px] font-bold text-slate-600 uppercase">Ctrl+Enter</kbd>
              <span className="text-[9px] text-slate-700">= Run</span>
            </div>
          </div>

          {/* Monaco Editor — fills remaining height */}
          <div className="flex-1 overflow-hidden">
            <Editor
              height="100%"
              language={currentLang.monacoId}
              value={code}
              onChange={handleCodeChange}
              onMount={handleEditorMount}
              theme="skilltree-dark"
              options={{
                fontSize: 14,
                fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
                fontLigatures: true,
                minimap: { enabled: false },
                lineNumbers: 'on',
                wordWrap: 'off',
                autoIndent: 'full',
                matchBrackets: 'always',
                scrollBeyondLastLine: false,
                renderLineHighlight: 'line',
                cursorBlinking: 'smooth',
                cursorSmoothCaretAnimation: 'on',
                smoothScrolling: true,
                padding: { top: 16, bottom: 16 },
                tabSize: 4,
                insertSpaces: true,
                formatOnPaste: true,
                formatOnType: true,
                quickSuggestions: aiModeEnabled,
                parameterHints: { enabled: aiModeEnabled },
                scrollbar: { verticalScrollbarSize: 5, horizontalScrollbarSize: 5 },
              }}
              loading={
                <div className="flex items-center justify-center h-full bg-[#0a0c10]">
                  <Loader2 size={24} className="text-primary animate-spin" />
                </div>
              }
            />
          </div>
        </div>

        {/* ══ RIGHT — Info + Output 40% ══ */}
        <div className="flex flex-col overflow-y-auto" style={{ width: '40%' }}>

          {/* Quest description */}
          {quest && (
            <div className="border-b border-white/5 shrink-0">
              <button
                onClick={() => setQuestPanelOpen(v => !v)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/5 transition-colors duration-200"
              >
                <div className="flex items-center gap-2">
                  <Zap size={13} className="text-primary drop-shadow-[0_0_6px_rgba(99,102,241,0.8)]" />
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-300">Quest</span>
                  <span className="px-2 py-0.5 rounded-full bg-primary/20 border border-primary/30 text-[9px] font-black text-primary uppercase tracking-wider">{quest.xp_reward} XP</span>
                </div>
                {questPanelOpen ? <ChevronUp size={13} className="text-slate-500" /> : <ChevronDown size={13} className="text-slate-500" />}
              </button>
              <AnimatePresence>
                {questPanelOpen && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="px-4 pb-4 space-y-3">
                      <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">{quest.description}</p>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                          <Clock size={9} />{quest.estimated_minutes}m
                        </span>
                        <span className="px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-bold uppercase tracking-wider text-slate-400">{quest.type}</span>
                        {quest.skill_name && (
                          <span className="px-2.5 py-1 rounded-full bg-primary/10 border border-primary/20 text-[10px] font-bold uppercase tracking-wider text-primary">{quest.skill_name}</span>
                        )}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* Output panel */}
          <div className="flex flex-col border-b border-white/5 shrink-0">
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/5">
              <div className="flex items-center gap-2">
                <Terminal size={13} className="text-slate-500" />
                <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Output</span>
                {execTime !== null && (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-[9px] font-bold text-slate-500">
                    <Clock size={9} />{execTime}ms
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {/* Mobile status */}
                <div className="md:hidden">
                  <AnimatePresence mode="wait">
                    {execStatus !== 'idle' && <StatusBanner key={execStatus} execStatus={execStatus} />}
                  </AnimatePresence>
                </div>
                {execOutput && (
                  <button onClick={handleCopyOutput} className="flex items-center gap-1 px-2 py-1 rounded-lg bg-white/5 border border-white/10 text-[10px] font-bold text-slate-400 hover:bg-white/10 hover:text-white transition-all duration-200">
                    {copied ? <Check size={10} className="text-emerald-400" /> : <Copy size={10} />}
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                )}
              </div>
            </div>

            {/* Terminal output */}
            <div className="p-4 min-h-[100px] max-h-[180px] overflow-y-auto font-mono text-xs">
              {/* AI Simulation Banner */}
              {execOutput?.is_simulated && (
                <motion.div
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-2 px-3 py-2 mb-3 rounded-xl bg-primary/10 border border-primary/30 text-primary"
                >
                  <Bot size={12} className="shrink-0 drop-shadow-[0_0_6px_rgba(99,102,241,0.8)]" />
                  <span className="text-[10px] font-bold uppercase tracking-wider">AI Simulation - Not Real Execution</span>
                  <Sparkles size={10} className="ml-auto animate-pulse" />
                </motion.div>
              )}
              
              {isRunning && !execOutput && (
                <div className="flex items-center gap-2 text-primary">
                  <Loader2 size={12} className="animate-spin" />
                  <span>{aiModeEnabled ? 'AI analyzing code...' : 'Executing...'}</span>
                </div>
              )}
              {!isRunning && !execOutput && <p className="text-slate-600 italic">Run your code to see output here.</p>}
              {execOutput?.stdout && <pre className="text-emerald-400 whitespace-pre-wrap break-words leading-relaxed">{execOutput.stdout}</pre>}
              {execOutput?.stderr && <pre className="text-red-400 whitespace-pre-wrap break-words leading-relaxed mt-1">{execOutput.stderr}</pre>}
            </div>

            {/* Test cases */}
            {testResults.length > 0 && (
              <div className="border-t border-white/5">
                <div className="flex items-center justify-between px-4 py-2">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Test Cases</span>
                  <span className={cn('text-[10px] font-black uppercase tracking-wider', passedCount === testResults.length ? 'text-emerald-400' : 'text-red-400')}>
                    {passedCount}/{testResults.length} Passed
                  </span>
                </div>
                <div className="overflow-x-auto max-h-[180px] overflow-y-auto">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="border-b border-white/5">
                        {['Input', 'Expected', 'Actual', 'Status'].map(h => (
                          <th key={h} className="px-3 py-2 text-[9px] font-black uppercase tracking-widest text-slate-600">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {testResults.map((tc, i) => <TestCaseRow key={i} tc={tc} index={i} />)}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* AI Feedback */}
          <div className="p-4 shrink-0">
            <AnimatePresence>
              {(aiFeedback || detectionScore !== undefined) && (
                <AiFeedbackPanel feedback={aiFeedback} detectionScore={detectionScore} />
              )}
            </AnimatePresence>
            {!aiFeedback && detectionScore === undefined && (
              <div className="glass-card rounded-2xl p-4 text-center">
                <Sparkles size={18} className="text-slate-600 mx-auto mb-2" />
                <p className="text-xs text-slate-600">Submit your solution to receive AI feedback.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Nav */}
      <BottomNav />
    </div>
  );
}

export default EditorPage;
