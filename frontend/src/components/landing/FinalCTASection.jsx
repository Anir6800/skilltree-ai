/**
 * FinalCTASection Component
 * Full-width CTA with animated gradient background and email capture
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check } from 'lucide-react';

const FinalCTASection = () => {
  const [email, setEmail] = useState('');
  const [counts, setCounts] = useState({
    developers: 0,
    quests: 0,
    improvement: 0,
    rating: 0,
  });
  const [hasAnimated, setHasAnimated] = useState(false);
  const sectionRef = useRef(null);
  const navigate = useNavigate();

  const finalValues = {
    developers: 12400,
    quests: 850000,
    improvement: 94,
    rating: 4.9,
  };

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated) {
          setHasAnimated(true);
          animateCounters();
        }
      },
      { threshold: 0.5 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => {
      if (sectionRef.current) {
        observer.unobserve(sectionRef.current);
      }
    };
  }, [hasAnimated]);

  const animateCounters = () => {
    const duration = 1500;
    const startTime = performance.now();

    const easeOutQuad = (t) => t * (2 - t);

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = easeOutQuad(progress);

      setCounts({
        developers: Math.floor(finalValues.developers * easedProgress),
        quests: Math.floor(finalValues.quests * easedProgress),
        improvement: Math.floor(finalValues.improvement * easedProgress),
        rating: parseFloat((finalValues.rating * easedProgress).toFixed(1)),
      });

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  };

  const formatNumber = (num) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (email) {
      navigate(`/register?email=${encodeURIComponent(email)}`);
    } else {
      navigate('/register');
    }
  };

  return (
    <section
      ref={sectionRef}
      className="relative min-h-[400px] flex items-center justify-center overflow-hidden py-24 px-6"
    >
      {/* Animated Gradient Background */}
      <div className="absolute inset-0 animated-gradient-bg" />

      {/* Content */}
      <div className="relative z-10 max-w-4xl mx-auto text-center">
        {/* Headline */}
        <h2 className="text-5xl md:text-[52px] font-[800] tracking-[-2px] text-white mb-6 leading-tight">
          Your skill tree is waiting.
        </h2>

        {/* Subtext */}
        <p className="text-lg text-slate-300 mb-8 max-w-2xl mx-auto leading-relaxed">
          Join 12,400+ developers who stopped grinding aimlessly and started growing with purpose.
        </p>

        {/* Email Capture Form */}
        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-6 max-w-xl mx-auto">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            className="w-full sm:flex-1 px-6 py-4 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 backdrop-blur-sm transition-all"
          />
          <button
            type="submit"
            className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-purple-600 to-purple-800 text-white font-bold rounded-lg hover:shadow-[0_0_30px_rgba(124,106,245,0.5)] transition-all whitespace-nowrap"
          >
            Get Started Free →
          </button>
        </form>

        {/* Benefits */}
        <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-slate-400 mb-12">
          <div className="flex items-center space-x-2">
            <Check size={16} className="text-green-400" />
            <span>Free forever plan</span>
          </div>
          <div className="flex items-center space-x-2">
            <Check size={16} className="text-green-400" />
            <span>No credit card</span>
          </div>
          <div className="flex items-center space-x-2">
            <Check size={16} className="text-green-400" />
            <span>Cancel anytime</span>
          </div>
        </div>

        {/* Stats Counters */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-3xl mx-auto">
          <div className="text-center">
            <div className="text-3xl font-mono font-bold text-white mb-1">
              {formatNumber(counts.developers)}+
            </div>
            <div className="text-xs text-slate-400 uppercase tracking-wider">Developers</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-mono font-bold text-white mb-1">
              {formatNumber(counts.quests)}+
            </div>
            <div className="text-xs text-slate-400 uppercase tracking-wider">Quests Completed</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-mono font-bold text-white mb-1">
              {counts.improvement}%
            </div>
            <div className="text-xs text-slate-400 uppercase tracking-wider">Skill Improvement</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-mono font-bold text-white mb-1">
              {counts.rating.toFixed(1)}★
            </div>
            <div className="text-xs text-slate-400 uppercase tracking-wider">Avg Rating</div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes gradient-shift {
          0% {
            background: radial-gradient(
              circle at 20% 50%,
              rgba(124, 106, 245, 0.15) 0%,
              rgba(56, 217, 217, 0.08) 50%,
              rgba(224, 106, 172, 0.08) 100%
            );
          }
          33% {
            background: radial-gradient(
              circle at 80% 50%,
              rgba(56, 217, 217, 0.15) 0%,
              rgba(224, 106, 172, 0.08) 50%,
              rgba(124, 106, 245, 0.08) 100%
            );
          }
          66% {
            background: radial-gradient(
              circle at 50% 80%,
              rgba(224, 106, 172, 0.15) 0%,
              rgba(124, 106, 245, 0.08) 50%,
              rgba(56, 217, 217, 0.08) 100%
            );
          }
          100% {
            background: radial-gradient(
              circle at 20% 50%,
              rgba(124, 106, 245, 0.15) 0%,
              rgba(56, 217, 217, 0.08) 50%,
              rgba(224, 106, 172, 0.08) 100%
            );
          }
        }

        .animated-gradient-bg {
          animation: gradient-shift 8s ease infinite;
        }
      `}</style>
    </section>
  );
};

export default FinalCTASection;
