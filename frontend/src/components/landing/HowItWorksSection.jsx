/**
 * HowItWorksSection Component
 * Three steps wired along a single circuit path with a traveling pulse dot
 * that animates once the section enters view.
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { GitBranch, ScanSearch, Swords } from 'lucide-react';
import useScrollAnimation from '../../hooks/useScrollAnimation';

const steps = [
  {
    icon: ScanSearch,
    tag: 'Takes 2 minutes',
    title: 'Scan your current graph',
    text: 'Six questions about your target role, current level per category, and hours per week. That\'s the whole input.',
  },
  {
    icon: GitBranch,
    tag: 'Instant generation',
    title: 'Route your skill tree',
    text: 'AI wires a dependency graph from what you already know to what you need — skipping nodes you\'ve already earned.',
  },
  {
    icon: Swords,
    tag: 'Compounds fast',
    title: 'Light up each node',
    text: 'Solve AI-graded quests, race live opponents, and watch verified nodes light up red across your tree.',
  },
];

const HowItWorksSection = () => {
  const { ref, isVisible, className } = useScrollAnimation({ threshold: 0.3 });
  const [pulseStep, setPulseStep] = useState(-1);

  useEffect(() => {
    if (!isVisible) return;
    steps.forEach((_, idx) => {
      setTimeout(() => setPulseStep(idx), idx * 500 + 300);
    });
  }, [isVisible]);

  return (
    <section
      id="how-it-works"
      ref={ref}
      className={`relative py-24 px-6 bg-gradient-to-b from-[#0a0a0a] to-[#050505] ${className} animate-in-default`}
    >
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-20">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm mb-4">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              ✦ THE CIRCUIT
            </span>
          </div>
          <h2 className="text-5xl font-black tracking-tighter mb-4 text-white">
            Three nodes. One closed loop.
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            No guesswork, no generic content — a path traced by AI around your exact gaps.
          </p>
        </div>

        {/* Circuit Path */}
        <div className="relative">
          <div className="hidden lg:block absolute top-8 left-[16.5%] right-[16.5%] h-px">
            <svg className="absolute inset-0 w-full h-full overflow-visible" preserveAspectRatio="none">
              <line x1="0" y1="0" x2="100%" y2="0" stroke="rgba(255,255,255,0.08)" strokeWidth="2" />
              <line
                x1="0"
                y1="0"
                x2="100%"
                y2="0"
                stroke="#ff2d2d"
                strokeWidth="2"
                strokeDasharray="1000"
                strokeDashoffset={isVisible ? 0 : 1000}
                style={{ transition: 'stroke-dashoffset 1.4s ease-out 0.2s' }}
              />
            </svg>
          </div>

          <div className="grid lg:grid-cols-3 gap-12 lg:gap-8">
            {steps.map((step, idx) => (
              <div key={step.title} className="relative flex flex-col items-center text-center">
                <div
                  className={`w-16 h-16 rounded-full flex items-center justify-center mb-6 relative z-10 border-2 transition-all duration-500 ${
                    pulseStep >= idx
                      ? 'bg-red-500/15 border-red-500 shadow-[0_0_30px_rgba(255,45,45,0.4)]'
                      : 'bg-white/5 border-white/15'
                  }`}
                >
                  <step.icon size={26} className={pulseStep >= idx ? 'text-red-400' : 'text-slate-500'} />
                </div>

                <div className="inline-flex items-center px-3 py-1 bg-red-500/10 border border-red-500/25 rounded-full mb-3">
                  <span className="text-xs font-semibold text-red-300">{step.tag}</span>
                </div>
                <h3 className="text-xl font-black text-white mb-3">{step.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed max-w-xs">{step.text}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="text-center mt-20">
          <Link
            to="/register"
            className="magnetic-btn inline-flex items-center space-x-2 px-8 py-4 bg-red-600 hover:bg-red-500 text-white font-bold text-lg rounded-lg hover:shadow-[0_0_40px_rgba(255,45,45,0.4)] transition-all"
          >
            <span>Close my first loop →</span>
          </Link>
        </div>
      </div>
    </section>
  );
};

export default HowItWorksSection;
