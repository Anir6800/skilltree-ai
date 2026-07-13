/**
 * FeaturesSection Component
 * Features rendered as circuit nodes branching left/right off a vertical spine,
 * echoing the logo's tree structure.
 */

import { Cpu, GitMerge, MessageSquareCode, Swords, Trophy } from 'lucide-react';
import useScrollAnimation from '../../hooks/useScrollAnimation';

const nodes = [
  {
    icon: GitMerge,
    title: 'Skill graph, not a syllabus',
    text: 'A live dependency graph of every skill you need, wired by AI from your goals — skip what you already know.',
    side: 'left',
  },
  {
    icon: Cpu,
    title: 'Five-language sandbox',
    text: 'Python, JS, C++, Java, Go — compiled in an isolated container the moment you hit run. No setup.',
    side: 'right',
  },
  {
    icon: Swords,
    title: 'Live coding races',
    text: 'Race another developer solving the same problem in real time. First clean pass wins the node.',
    side: 'left',
  },
  {
    icon: MessageSquareCode,
    title: 'Context-aware AI mentor',
    text: 'Ask anything. It already knows what you\'ve completed, and answers against your actual history.',
    side: 'right',
  },
  {
    icon: Trophy,
    title: 'Global leaderboard',
    text: 'Compete on XP earned per verified skill, not time spent. Weekly resets keep it honest.',
    side: 'left',
  },
];

const FeaturesSection = () => {
  const { ref, className } = useScrollAnimation({ threshold: 0.15 });

  return (
    <section
      id="features"
      ref={ref}
      className={`relative py-24 px-6 bg-[#0a0a0a] ${className} animate-in-default`}
    >
      <div className="max-w-5xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-20">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm mb-4">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              ✦ THE GRAPH
            </span>
          </div>
          <h2 className="text-5xl font-black tracking-tighter mb-4 text-white">
            Every node earns its place.
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            No filler modules. Every feature exists to move you one verified node closer to the skill you're after.
          </p>
        </div>

        {/* Spine + Nodes */}
        <div className="relative">
          <div className="hidden md:block absolute left-1/2 top-0 bottom-0 w-px -translate-x-1/2 bg-gradient-to-b from-transparent via-red-500/30 to-transparent" />

          <div className="space-y-10 md:space-y-4">
            {nodes.map((node, idx) => (
              <div
                key={node.title}
                className={`relative md:grid md:grid-cols-2 md:gap-12 items-center`}
              >
                {/* Connector dot on spine */}
                <div className="hidden md:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-red-500 shadow-[0_0_16px_rgba(255,45,45,0.6)] z-10" />

                <div className={node.side === 'left' ? 'md:pr-16 md:text-right' : 'md:col-start-2 md:pl-16'}>
                  <div
                    className={`group bg-white/[0.03] border border-white/10 rounded-2xl p-6 transition-all duration-300 hover:border-red-500/40 hover:bg-white/[0.05] hover:shadow-[0_20px_40px_rgba(255,45,45,0.1)] ${
                      node.side === 'left' ? 'md:ml-auto' : ''
                    }`}
                  >
                    <div className={`flex items-center gap-3 mb-3 ${node.side === 'left' ? 'md:flex-row-reverse' : ''}`}>
                      <div className="w-10 h-10 rounded-lg bg-red-500/15 text-red-400 flex items-center justify-center flex-shrink-0 transition-transform duration-300 group-hover:-translate-y-1">
                        <node.icon size={20} />
                      </div>
                      <h3 className="text-lg font-bold text-white">{node.title}</h3>
                    </div>
                    <p className="text-sm text-slate-400 leading-relaxed">{node.text}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
