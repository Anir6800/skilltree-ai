import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Bot, Code2, GitBranch, Sparkles, Target, Users, Zap } from 'lucide-react';
import LandingNav from '../components/landing/LandingNav';
import LandingFooter from '../components/landing/LandingFooter';
import '../styles/landing.css';

const stats = [
  { value: '4', label: 'learning modes' },
  { value: '24/7', label: 'mentor support' },
  { value: 'AI', label: 'adaptive paths' },
];

const values = [
  {
    icon: Target,
    title: 'Focused progression',
    text: 'Every skill path is built around concrete outcomes, practical quests, and visible progress.',
  },
  {
    icon: Bot,
    title: 'Adaptive guidance',
    text: 'The mentor layer uses your activity to suggest the next useful step instead of a generic curriculum.',
  },
  {
    icon: Users,
    title: 'Community practice',
    text: 'Groups, shared solutions, and multiplayer challenges turn learning into repeated, social practice.',
  },
];

const AboutPage = () => {
  return (
    <div className="min-h-screen bg-[#0a0c10] text-white overflow-x-hidden">
      <LandingNav />

      <main className="pt-[60px]">
        <section className="relative min-h-[78vh] flex items-center border-b border-white/5 overflow-hidden">
          <div className="absolute inset-0 hero-gradient" />
          <div className="absolute inset-0 opacity-30 bg-[linear-gradient(rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.04)_1px,transparent_1px)] bg-[size:72px_72px]" />

          <div className="relative max-w-7xl mx-auto px-6 py-20 grid lg:grid-cols-[1fr_0.8fr] gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-purple-500/30 bg-purple-500/10 text-purple-200 text-xs font-bold uppercase tracking-widest mb-6">
                <Sparkles size={14} />
                About SkillTree.AI
              </div>
              <h1 className="text-5xl md:text-7xl font-black tracking-tighter leading-[0.95] mb-6">
                A skill platform built for builders.
              </h1>
              <p className="text-lg md:text-xl text-slate-300 max-w-2xl leading-relaxed mb-8">
                SkillTree.AI combines adaptive learning paths, quest-based practice, AI mentoring,
                and competitive coding workflows so learners can move from curiosity to capability.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link to="/register" className="btn-primary inline-flex items-center justify-center gap-2">
                  Start learning
                  <ArrowRight size={18} />
                </Link>
                <Link to="/contact" className="btn-secondary inline-flex items-center justify-center">
                  Contact us
                </Link>
              </div>
            </div>

            <div className="glass-panel rounded-2xl p-6 md:p-8">
              <div className="grid grid-cols-3 gap-4 mb-8">
                {stats.map((stat) => (
                  <div key={stat.label} className="bg-white/5 border border-white/10 rounded-xl p-4">
                    <div className="text-2xl font-black text-white">{stat.value}</div>
                    <div className="text-xs text-slate-500 uppercase tracking-widest mt-1">{stat.label}</div>
                  </div>
                ))}
              </div>
              <div className="space-y-4">
                {[
                  { icon: GitBranch, label: 'AI-generated skill trees' },
                  { icon: Code2, label: 'Quest and editor workflows' },
                  { icon: Zap, label: 'XP, reports, badges, and streaks' },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-4 rounded-xl bg-black/30 border border-white/10 p-4">
                    <div className="w-10 h-10 rounded-lg bg-purple-500/15 text-purple-300 flex items-center justify-center">
                      <item.icon size={20} />
                    </div>
                    <span className="font-semibold text-slate-200">{item.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="max-w-7xl mx-auto px-6 py-20">
          <div className="grid lg:grid-cols-[0.7fr_1fr] gap-12">
            <div>
              <p className="text-sm font-bold text-purple-300 uppercase tracking-widest mb-3">Our mission</p>
              <h2 className="text-4xl md:text-5xl font-black tracking-tighter mb-5">
                Make technical growth measurable, personal, and practical.
              </h2>
              <p className="text-slate-400 leading-relaxed">
                The product is designed around active learning: generate a path, complete quests,
                review feedback, compare solutions, and keep improving through repetition.
              </p>
            </div>
            <div className="grid md:grid-cols-3 gap-5">
              {values.map((value) => (
                <div key={value.title} className="bento-card rounded-xl">
                  <value.icon className="bento-icon text-purple-300 mb-5" size={32} />
                  <h3 className="text-lg font-bold text-white mb-3">{value.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{value.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <LandingFooter />
    </div>
  );
};

export default AboutPage;
