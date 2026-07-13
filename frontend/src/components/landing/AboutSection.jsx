/**
 * AboutSection Component
 * Manifesto-style about block with a circuit-trace stat rail.
 */

import { Compass, Layers, Radar } from 'lucide-react';
import useScrollAnimation from '../../hooks/useScrollAnimation';

const principles = [
  {
    icon: Radar,
    title: 'Diagnose, don\'t guess',
    text: 'We trace what you already know before deciding what to teach — most platforms skip this step entirely.',
  },
  {
    icon: Layers,
    title: 'Dependencies over lists',
    text: 'Skills unlock skills. The graph enforces prerequisites so you never learn something out of order.',
  },
  {
    icon: Compass,
    title: 'Built to be finished',
    text: 'Every path is sized to a real number of hours and a real endpoint — not an infinite backlog.',
  },
];

const AboutSection = () => {
  const { ref, className } = useScrollAnimation({ threshold: 0.2 });

  return (
    <section
      id="about"
      ref={ref}
      className={`relative py-24 px-6 bg-[#050505] overflow-hidden ${className} animate-in-default`}
    >
      {/* Faint corner circuit trace */}
      <svg
        className="absolute -right-20 -top-20 w-[420px] h-[420px] opacity-[0.06] pointer-events-none"
        viewBox="0 0 400 400"
      >
        <circle cx="200" cy="200" r="6" fill="#ff2d2d" />
        <line x1="200" y1="200" x2="80" y2="120" stroke="#ff2d2d" strokeWidth="2" />
        <line x1="200" y1="200" x2="320" y2="90" stroke="#ff2d2d" strokeWidth="2" />
        <line x1="200" y1="200" x2="340" y2="280" stroke="#ff2d2d" strokeWidth="2" />
        <circle cx="80" cy="120" r="4" fill="#ff2d2d" />
        <circle cx="320" cy="90" r="4" fill="#ff2d2d" />
        <circle cx="340" cy="280" r="4" fill="#ff2d2d" />
      </svg>

      <div className="max-w-6xl mx-auto relative">
        <div className="grid lg:grid-cols-[0.8fr_1fr] gap-16 items-start">
          <div>
            <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm mb-4">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                ✦ WHY THIS EXISTS
              </span>
            </div>
            <h2 className="text-5xl font-black tracking-tighter mb-6 text-white leading-[1.05]">
              Learning platforms give you content.
              <br />
              <span className="text-red-500">We give you a route.</span>
            </h2>
            <p className="text-slate-400 leading-relaxed">
              Most platforms hand every learner the same syllabus regardless of what they already
              know. SkillTree AI treats your knowledge as a graph — it finds the shortest verified
              path from where you actually stand to the role you're aiming for.
            </p>
          </div>

          <div className="space-y-5">
            {principles.map((p) => (
              <div
                key={p.title}
                className="group flex items-start gap-5 bg-white/[0.03] border border-white/10 rounded-2xl p-6 transition-all duration-300 hover:border-red-500/30 hover:bg-white/[0.05]"
              >
                <div className="w-11 h-11 rounded-xl bg-red-500/15 text-red-400 flex items-center justify-center flex-shrink-0 transition-transform duration-300 group-hover:-translate-y-1">
                  <p.icon size={22} />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white mb-1.5">{p.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{p.text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default AboutSection;
