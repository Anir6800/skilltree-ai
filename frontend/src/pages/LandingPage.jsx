/**
 * SkillTree AI - Landing Page
 * Single-page flow: Hero, Features, How It Works, About, Contact.
 * No persistent header/footer — a floating pill nav appears on scroll.
 */

import  { useEffect, useRef } from 'react';
import FloatingNav from '../components/landing/FloatingNav';
import HeroSection from '../components/landing/HeroSection';
import FeaturesSection from '../components/landing/FeaturesSection';
import HowItWorksSection from '../components/landing/HowItWorksSection';
import AboutSection from '../components/landing/AboutSection';
import ContactSection from '../components/landing/ContactSection';
import '../styles/landing.css';

const LandingPage = () => {
  const glowRef = useRef(null);

  useEffect(() => {
    if (!window.location.hash) {
      return;
    }

    const element = document.getElementById(window.location.hash.slice(1));
    if (element) {
      window.requestAnimationFrame(() => {
        element.scrollIntoView({ behavior: 'smooth' });
      });
    }
  }, []);

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const handlePointerMove = (e) => {
      const glow = glowRef.current;
      if (!glow) return;
      glow.style.transform = `translate(${e.clientX}px, ${e.clientY}px) translate(-50%, -50%)`;
    };

    window.addEventListener('pointermove', handlePointerMove);
    return () => window.removeEventListener('pointermove', handlePointerMove);
  }, []);

  return (
    <div className="min-h-screen bg-[#050505] text-white overflow-x-hidden">
      <div ref={glowRef} className="cursor-glow hidden md:block" />
      <FloatingNav />
      <HeroSection />
      <FeaturesSection />
      <HowItWorksSection />
      <AboutSection />
      <ContactSection />
    </div>
  );
};

export default LandingPage;
