/**
 * FloatingNav Component
 * Minimal floating pill nav — logo mark + section anchors, no full-width header
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import logoMark from '../../assets/skilltree-icon.png';

const sections = [
  { label: 'Features', id: 'features' },
  { label: 'How It Works', id: 'how-it-works' },
  { label: 'About', id: 'about' },
  { label: 'Contact', id: 'contact' },
];

const FloatingNav = () => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => setVisible(window.scrollY > 300);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div
      className={`fixed top-5 left-1/2 -translate-x-1/2 z-50 transition-all duration-500 ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4 pointer-events-none'
      }`}
    >
      <div className="flex items-center gap-1 pl-2 pr-2 py-2 rounded-full bg-[rgba(5,5,5,0.85)] backdrop-blur-[20px] border border-white/10 shadow-[0_8px_30px_rgba(0,0,0,0.5)]">
        <Link to="/" className="w-8 h-8 rounded-full overflow-hidden bg-black flex items-center justify-center mr-1">
          <img
            src={logoMark}
            alt="SkillTree AI"
            className="w-full h-full object-cover"
          />
        </Link>
        {sections.map((s) => (
          <button
            key={s.id}
            onClick={() => scrollToSection(s.id)}
            className="px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-white rounded-full hover:bg-white/5 transition-colors"
          >
            {s.label}
          </button>
        ))}
        <Link
          to="/register"
          className="magnetic-btn ml-1 px-4 py-1.5 bg-red-600 hover:bg-red-500 text-white text-xs font-semibold rounded-full transition-colors"
        >
          Start Free
        </Link>
      </div>
    </div>
  );
};

export default FloatingNav;
