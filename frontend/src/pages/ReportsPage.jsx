/**
 * SkillTree AI - Weekly Reports Page
 * View, generate, and download AI-generated weekly progress reports.
 * Redesigned with glassmorphism design system.
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart2, Download, Eye, Zap, Target, Trophy,
  Loader2, AlertCircle, Sparkles, X, TrendingUp,
} from 'lucide-react';
import api from '../api/api';
import MainLayout from '../components/layout/MainLayout';

const StatCard = ({ label, value, color = 'text-white' }) => (
  <div className="glass-card p-4 rounded-2xl">
    <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">{label}</div>
    <div className={`text-2xl font-black ${color}`}>{value}</div>
  </div>
);

const ReportsPage = () => {
  const [reports, setReports] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchReports();
    fetchStats();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await api.get('/api/reports/');
      setReports(response.data.results || response.data);
    } catch (err) {
      setError('Failed to load reports.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api.get('/api/reports/stats/');
      setStats(response.data);
    } catch { /* silent */ }
  };

  const handleGenerateReport = async () => {
    setGenerating(true);
    setError(null);
    try {
      await api.post('/api/reports/generate/');
      setTimeout(() => {
        fetchReports();
        fetchStats();
        setGenerating(false);
      }, 2000);
    } catch (err) {
      setError('Failed to generate report. Please try again.');
      setGenerating(false);
    }
  };

  const handleDownloadPDF = async (reportId) => {
    try {
      const response = await api.get(`/api/reports/${reportId}/download/`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `weekly_report_${reportId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch { /* silent */ }
  };

  return (
    <MainLayout>
      <div className="min-h-screen bg-[#0a0c10] text-white p-4 md:p-8 max-w-5xl mx-auto">
        {/* Background glows */}
        <div className="fixed inset-0 pointer-events-none -z-10">
          <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
          <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
        </div>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 border border-primary/30 flex items-center justify-center">
              <BarChart2 size={22} className="text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tight">Weekly Reports</h1>
              <p className="text-slate-400 text-sm">Track your progress and growth over time</p>
            </div>
          </div>
        </motion.div>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm mb-6"
            >
              <AlertCircle size={16} /> {error}
              <button onClick={() => setError(null)} className="ml-auto"><X size={14} /></button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Latest report highlight */}
        {stats?.latest_report && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-panel p-6 rounded-3xl mb-8 border-primary/20 shadow-[0_0_40px_rgba(99,102,241,0.08)]"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-black flex items-center gap-2">
                  <Sparkles size={18} className="text-primary" /> Your Week in Review
                </h2>
                <p className="text-slate-400 text-sm">Week {stats.latest_report.week_number}</p>
              </div>
              <button
                onClick={() => handleDownloadPDF(stats.latest_report.id)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-bold text-sm hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all"
              >
                <Download size={15} /> Download PDF
              </button>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-4">
              <StatCard label="XP Earned" value={stats.latest_report.xp_earned} color="text-emerald-400" />
              <StatCard label="Quests Passed" value={stats.latest_report.quests_passed} color="text-blue-400" />
              <StatCard label="Win Rate" value={`${stats.latest_report.win_rate}%`} color="text-amber-400" />
            </div>

            <button
              onClick={() => setSelectedReport(stats.latest_report)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary/10 border border-primary/30 text-primary font-bold text-sm hover:bg-primary/20 transition-all"
            >
              <Eye size={15} /> View Summary
            </button>
          </motion.div>
        )}

        {/* Generate button */}
        <div className="mb-8">
          <button
            onClick={handleGenerateReport}
            disabled={generating}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-bold text-sm uppercase tracking-wider hover:shadow-[0_0_20px_rgba(16,185,129,0.4)] disabled:opacity-60 disabled:cursor-not-allowed transition-all"
          >
            {generating ? <Loader2 size={16} className="animate-spin" /> : <TrendingUp size={16} />}
            {generating ? 'Generating...' : 'Generate Report Now'}
          </button>
        </div>

        {/* Reports list */}
        <div>
          <h2 className="text-xl font-black mb-4">Past Reports</h2>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 size={32} className="animate-spin text-primary" />
            </div>
          ) : reports.length === 0 ? (
            <div className="glass-panel p-12 rounded-3xl text-center border-dashed border-white/10">
              <BarChart2 size={40} className="text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-black text-slate-300 mb-2">No Reports Yet</h3>
              <p className="text-slate-500 text-sm">Your first weekly report will be generated next Monday.</p>
            </div>
          ) : (
            <div className="space-y-3">
              <AnimatePresence>
                {reports.map((report, idx) => (
                  <motion.div
                    key={report.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ delay: idx * 0.04 }}
                    className="glass-panel p-5 rounded-2xl flex items-center justify-between gap-4"
                  >
                    <div>
                      <h3 className="text-base font-black text-white mb-1">Week {report.week_number}</h3>
                      <p className="text-xs text-slate-400">
                        Generated {new Date(report.generated_at).toLocaleDateString()}
                        {report.viewed_at && ` · Viewed ${new Date(report.viewed_at).toLocaleDateString()}`}
                      </p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <button
                        onClick={() => setSelectedReport(report)}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-primary/10 border border-primary/30 text-primary font-bold text-xs hover:bg-primary/20 transition-all"
                      >
                        <Eye size={13} /> Summary
                      </button>
                      <button
                        onClick={() => handleDownloadPDF(report.id)}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-bold text-xs hover:shadow-[0_0_16px_rgba(99,102,241,0.4)] transition-all"
                      >
                        <Download size={13} /> PDF
                      </button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>

      {/* Summary Modal */}
      <AnimatePresence>
        {selectedReport && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedReport(null)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="glass-panel p-8 rounded-3xl w-full max-w-lg max-h-[80vh] overflow-y-auto border-primary/20"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-black">Week {selectedReport.week_number} Summary</h2>
                <button
                  onClick={() => setSelectedReport(null)}
                  className="p-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all"
                >
                  <X size={16} />
                </button>
              </div>

              {selectedReport.narrative && (
                <div className="space-y-5 mb-6">
                  {[
                    { label: '✨ Your Week', key: 'opening_sentence' },
                    { label: '📊 Skill Analysis', key: 'skill_analysis' },
                    { label: '🚀 Next Week', key: 'motivational_close' },
                  ].map(({ label, key }) => selectedReport.narrative[key] && (
                    <div key={key}>
                      <h3 className="text-sm font-black text-primary mb-2">{label}</h3>
                      <p className="text-sm text-slate-300 leading-relaxed">{selectedReport.narrative[key]}</p>
                    </div>
                  ))}
                </div>
              )}

              {selectedReport.data && (
                <div className="mb-6">
                  <h3 className="text-sm font-black text-primary mb-3">📈 Stats</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <StatCard label="XP Earned" value={selectedReport.data.xp_earned} color="text-emerald-400" />
                    <StatCard label="Quests Passed" value={selectedReport.data.quests_passed} color="text-blue-400" />
                    <StatCard label="Skills Unlocked" value={selectedReport.data.skills_unlocked} color="text-amber-400" />
                    <StatCard label="Win Rate" value={`${selectedReport.data.win_rate}%`} color="text-pink-400" />
                  </div>
                </div>
              )}

              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setSelectedReport(null)}
                  className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-slate-300 font-bold text-sm hover:bg-white/10 transition-all"
                >
                  Close
                </button>
                <button
                  onClick={() => { handleDownloadPDF(selectedReport.id); setSelectedReport(null); }}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-bold text-sm hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all"
                >
                  <Download size={15} /> Download PDF
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </MainLayout>
  );
};

export default ReportsPage;
