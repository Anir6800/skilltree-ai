/**
 * SkillTree AI - Landing Page
 * Assembles all landing section components into a single scrollable page.
 */

import React, { useEffect } from 'react';
import LandingNav from '../components/landing/LandingNav';
import HeroSection from '../components/landing/HeroSection';
import SocialProofBar from '../components/landing/SocialProofBar';
import FeaturesSection from '../components/landing/FeaturesSection';
import HowItWorksSection from '../components/landing/HowItWorksSection';
import ProductDemoSection from '../components/landing/ProductDemoSection';
import TestimonialsSection from '../components/landing/TestimonialsSection';
import PricingSection from '../components/landing/PricingSection';
import FinalCTASection from '../components/landing/FinalCTASection';
import LandingFooter from '../components/landing/LandingFooter';
import '../styles/landing.css';

const LandingPage = () => {
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

  return (
    <div className="min-h-screen bg-[#0a0c10] text-white overflow-x-hidden">
      <LandingNav />
      <HeroSection />
      <SocialProofBar />
      <FeaturesSection />
      <HowItWorksSection />
      <ProductDemoSection />
      <TestimonialsSection />
      <PricingSection />
      <FinalCTASection />
      <LandingFooter />
    </div>
  );
};

export default LandingPage;
