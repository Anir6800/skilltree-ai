/**
 * SocialProofBar Component
 * Trust-building strip with animated counters and company logo ticker
 */

import React, { useEffect, useRef, useState } from 'react';

const SocialProofBar = () => {
  const [hasAnimated, setHasAnimated] = useState(false);
  const [counts, setCounts] = useState({
    developers: 0,
    quests: 0,
    improvement: 0,
    rating: 0,
  });
  const sectionRef = useRef(null);

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

  const companies = [
    'Google',
    'Meta',
    'Stripe',
    'Airbnb',
    'Netflix',
    'OpenAI',
    'Shopify',
    'Figma',
    'Amazon',
    'Microsoft',
  ];

  return (
    <section
      ref={sectionRef}
      className="relative w-full bg-[#0f1117] border-t border-b border-white/5"
      style={{ height: '80px' }}
    >
      <div className="max-w-7xl mx-auto px-6 h-full">
        {/* Row 1: Animated Counters */}
        <div className="flex items-center justify-center h-1/2 border-b border-white/5">
          <div className="flex items-center divide-x divide-white/10">
            {/* Stat 1: Developers */}
            <div className="px-8 text-center">
              <div className="text-[20px] font-mono font-bold text-white counter-stat">
                {formatNumber(counts.developers)}+
              </div>
              <div className="text-[11px] text-slate-500 uppercase tracking-wider mt-0.5">
                Developers
              </div>
            </div>

            {/* Stat 2: Quests Completed */}
            <div className="px-8 text-center">
              <div className="text-[20px] font-mono font-bold text-white counter-stat">
                {formatNumber(counts.quests)}+
              </div>
              <div className="text-[11px] text-slate-500 uppercase tracking-wider mt-0.5">
                Quests Completed
              </div>
            </div>

            {/* Stat 3: Skill Improvement */}
            <div className="px-8 text-center">
              <div className="text-[20px] font-mono font-bold text-white counter-stat">
                {counts.improvement}%
              </div>
              <div className="text-[11px] text-slate-500 uppercase tracking-wider mt-0.5">
                Skill Improvement
              </div>
            </div>

            {/* Stat 4: Rating */}
            <div className="px-8 text-center">
              <div className="text-[20px] font-mono font-bold text-white counter-stat">
                {counts.rating.toFixed(1)}★
              </div>
              <div className="text-[11px] text-slate-500 uppercase tracking-wider mt-0.5">
                Avg Rating
              </div>
            </div>
          </div>
        </div>

        {/* Row 2: Logo Ticker */}
        <div className="flex items-center h-1/2">
          <div className="text-[10px] uppercase font-mono text-slate-600 tracking-wider mr-6 whitespace-nowrap">
            Developers from
          </div>
          <div className="flex-1 overflow-hidden relative">
            <div className="flex animate-logo-scroll">
              {[...companies, ...companies, ...companies].map((company, index) => (
                <div
                  key={index}
                  className="inline-flex items-center px-6 mx-2 text-sm font-semibold text-slate-500 whitespace-nowrap transition-all duration-300 hover:text-white company-logo"
                  style={{
                    filter: 'grayscale(1)',
                    opacity: 0.4,
                  }}
                >
                  {company}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes logo-scroll {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-33.333%);
          }
        }

        .animate-logo-scroll {
          animation: logo-scroll 30s linear infinite;
        }

        .animate-logo-scroll:hover {
          animation-play-state: paused;
        }

        .company-logo:hover {
          filter: grayscale(0) !important;
          opacity: 1 !important;
        }
      `}</style>
    </section>
  );
};

export default SocialProofBar;
