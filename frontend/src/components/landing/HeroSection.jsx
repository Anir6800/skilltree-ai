/**
 * HeroSection Component
 * Circuit-tree hero: branching SVG trunk grows from the logo mark, nodes pulse
 * outward, headline reveals as the circuit completes.
 */

import { Link } from 'react-router-dom';
import useMagneticHover from '../../hooks/useMagneticHover';
import logoMark from '../../assets/skilltree-icon.png';

const HeroSection = () => {
  const primaryCta = useMagneticHover(0.25);
  const secondaryCta = useMagneticHover(0.2);

  const scrollToSection = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-24 pb-20 px-6">
      {/* Faint dot grid */}
      <div className="absolute inset-0 opacity-[0.15] bg-[radial-gradient(rgba(255,255,255,0.4)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />

      {/* Radial glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: 'radial-gradient(circle at center, rgba(255, 45, 45, 0.14) 0%, transparent 60%)' }}
      />

      {/* Content */}
      <div className="relative z-10 max-w-[860px] mx-auto text-center">
        {/* Logo Mark */}
        <div className="w-20 h-20 mx-auto mb-8 rounded-2xl overflow-hidden bg-black border border-white/10 flex items-center justify-center shadow-[0_0_40px_rgba(255,45,45,0.3)]">
          <img
            src={logoMark}
            alt="SkillTree AI"
            className="w-full h-full object-cover"
          />
        </div>

        {/* Eyebrow Tag */}
        <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm mb-8 animate-in-default animate-in">
          <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            An adaptive skill graph, not a course list
          </span>
        </div>

        {/* H1 */}
        <h1 className="mb-6">
          <div className="text-[64px] md:text-[76px] leading-[1.02] font-[800] tracking-[-3px] flex flex-col items-center">
            <span className="text-white animate-in-default animate-in" style={{ animationDelay: '0ms' }}>
              Your knowledge,
            </span>
            <span
              className="text-transparent bg-clip-text bg-gradient-to-r from-[#ff2d2d] to-white animate-in-default animate-in"
              style={{ animationDelay: '80ms' }}
            >
              mapped like a circuit.
            </span>
          </div>
        </h1>

        {/* Subheadline */}
        <p
          className="text-[18px] text-slate-400 max-w-[540px] mx-auto mb-10 leading-relaxed animate-in-default animate-in"
          style={{ animationDelay: '400ms' }}
        >
          SkillTree AI traces what you already know, wires in what's missing, and routes you
          through the shortest real path to mastery — one traceable node at a time.
        </p>

        {/* CTA Row */}
        <div
          className="flex flex-col sm:flex-row items-center justify-center gap-3 animate-in-default animate-in"
          style={{ animationDelay: '600ms' }}
        >
          <Link
            ref={primaryCta.ref}
            onMouseMove={primaryCta.onMouseMove}
            onMouseLeave={primaryCta.onMouseLeave}
            to="/register"
            className="magnetic-btn px-8 py-[14px] bg-[#ff2d2d] text-white font-semibold text-base rounded-[10px] hover:bg-[#e42323] transition-colors hover:shadow-[0_0_30px_rgba(255,45,45,0.4)]"
          >
            Trace my skill graph →
          </Link>
          <button
            ref={secondaryCta.ref}
            onMouseMove={secondaryCta.onMouseMove}
            onMouseLeave={secondaryCta.onMouseLeave}
            onClick={() => scrollToSection('how-it-works')}
            className="magnetic-btn px-8 py-[14px] bg-transparent text-white font-semibold text-base rounded-[10px] border border-white/20 hover:bg-white/5 transition-colors"
          >
            See how it routes ↓
          </button>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
