/**
 * PricingSection Component
 * Pricing tiers with animated billing toggle and feature comparison
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Check, X } from 'lucide-react';
import useScrollAnimation from '../../hooks/useScrollAnimation';

const PricingSection = () => {
  const [isAnnual, setIsAnnual] = useState(false);
  const { ref, className } = useScrollAnimation({ threshold: 0.2 });

  const pricingTiers = [
    {
      name: 'Free',
      monthlyPrice: 0,
      annualPrice: 0,
      description: 'Perfect for getting started',
      features: [
        { text: '10 skills, 30 quests', included: true },
        { text: 'AI skill mapping (limited)', included: true },
        { text: 'Code execution (Python only)', included: true },
        { text: 'Global leaderboard view', included: true },
        { text: 'AI Mentor', included: false },
        { text: 'Multiplayer Arena', included: false },
        { text: 'Custom curriculum', included: false },
        { text: 'Admin access', included: false },
      ],
      cta: 'Start Free',
      ctaStyle: 'ghost',
      popular: false,
    },
    {
      name: 'Pro',
      monthlyPrice: 18,
      annualPrice: 11,
      description: 'For serious developers',
      features: [
        { text: 'All 50 skills, 180+ quests', included: true },
        { text: 'Full AI skill mapping', included: true },
        { text: 'All 5 languages', included: true },
        { text: 'AI Mentor (unlimited)', included: true },
        { text: 'Multiplayer Arena', included: true },
        { text: 'Personal curriculum', included: true },
        { text: 'Leaderboard + Streaks', included: true },
        { text: 'Admin content engine', included: false },
      ],
      cta: 'Start Pro →',
      ctaStyle: 'primary',
      popular: true,
    },
    {
      name: 'Team',
      monthlyPrice: 49,
      annualPrice: 29,
      description: 'Per 5 seats',
      features: [
        { text: 'Everything in Pro', included: true },
        { text: 'Admin content engine', included: true },
        { text: 'Custom skills & quests', included: true },
        { text: 'Team leaderboard', included: true },
        { text: 'LM Studio validation', included: true },
        { text: 'Bulk seat management', included: true },
        { text: 'Priority support', included: true },
      ],
      cta: 'Contact Sales',
      ctaStyle: 'amber',
      popular: false,
    },
  ];

  const getPrice = (tier) => {
    if (tier.monthlyPrice === 0) return '$0';
    const price = isAnnual ? tier.annualPrice : tier.monthlyPrice;
    return `$${price}`;
  };

  const getBillingPeriod = (tier) => {
    if (tier.monthlyPrice === 0) return '/mo forever';
    return isAnnual ? '/mo billed annually' : '/mo';
  };

  return (
    <section
      id="pricing"
      ref={ref}
      className={`relative py-24 px-6 bg-gradient-to-b from-[#0f1117] to-[#0a0c10] ${className} animate-in-default`}
    >
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm mb-4">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              ✦ PRICING
            </span>
          </div>
          <h2 className="text-5xl font-black tracking-tighter mb-4 text-white">
            Start free. Scale when you're ready.
          </h2>
          <p className="text-lg text-slate-400 mb-8">
            No credit card. No commitment. Cancel any time.
          </p>

          {/* Billing Toggle */}
          <div className="flex items-center justify-center space-x-4">
            <span className={`text-sm font-semibold transition-colors ${!isAnnual ? 'text-white' : 'text-slate-500'}`}>
              Monthly
            </span>
            <button
              onClick={() => setIsAnnual(!isAnnual)}
              className="relative w-16 h-8 bg-white/10 rounded-full border border-white/20 transition-all hover:border-purple-500/50"
            >
              <div
                className={`absolute top-1 left-1 w-6 h-6 bg-gradient-to-r from-purple-600 to-purple-800 rounded-full shadow-lg transition-transform duration-300 ${
                  isAnnual ? 'translate-x-8' : 'translate-x-0'
                }`}
              />
            </button>
            <span className={`text-sm font-semibold transition-colors ${isAnnual ? 'text-white' : 'text-slate-500'}`}>
              Annual
            </span>
            {isAnnual && (
              <span className="inline-flex items-center px-3 py-1 bg-green-500/20 border border-green-500/30 rounded-full text-xs font-bold text-green-400 animate-in-default animate-in">
                Save 40%
              </span>
            )}
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid lg:grid-cols-3 gap-8 mb-12">
          {pricingTiers.map((tier, index) => (
            <div
              key={index}
              className={`relative pricing-card ${
                tier.popular
                  ? 'bg-purple-500/5 border-2 border-purple-500 shadow-[0_0_40px_rgba(124,106,245,0.2)] pricing-card-popular'
                  : 'bg-white/5 border border-white/10'
              } rounded-2xl p-8 transition-all duration-300 hover:scale-105`}
            >
              {/* Popular Badge */}
              {tier.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <div className="px-4 py-1 bg-gradient-to-r from-purple-600 to-purple-800 rounded-full text-xs font-bold text-white uppercase tracking-wider shadow-lg">
                    Most Popular
                  </div>
                </div>
              )}

              {/* Tier Name */}
              <h3 className="text-2xl font-black text-white mb-2">{tier.name}</h3>
              <p className="text-sm text-slate-400 mb-6">{tier.description}</p>

              {/* Price */}
              <div className="mb-8">
                <div className="flex items-baseline">
                  <span className="text-5xl font-black text-white">{getPrice(tier)}</span>
                  <span className="text-slate-400 ml-2">{getBillingPeriod(tier)}</span>
                </div>
              </div>

              {/* Features */}
              <ul className="space-y-3 mb-8">
                {tier.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start space-x-3">
                    {feature.included ? (
                      <Check size={18} className="text-green-500 flex-shrink-0 mt-0.5" />
                    ) : (
                      <X size={18} className="text-slate-600 flex-shrink-0 mt-0.5" />
                    )}
                    <span className={`text-sm ${feature.included ? 'text-slate-300' : 'text-slate-600'}`}>
                      {feature.text}
                    </span>
                  </li>
                ))}
              </ul>

              {/* CTA Button */}
              <Link
                to={tier.name === 'Free' ? '/register' : tier.name === 'Team' ? '/contact' : '/register'}
                className={`block w-full py-3 text-center font-semibold rounded-lg transition-all ${
                  tier.ctaStyle === 'primary'
                    ? 'bg-gradient-to-r from-purple-600 to-purple-800 text-white hover:shadow-[0_0_30px_rgba(124,106,245,0.5)]'
                    : tier.ctaStyle === 'amber'
                    ? 'bg-transparent border border-amber-500/50 text-amber-400 hover:bg-amber-500/10'
                    : 'bg-transparent border border-white/20 text-white hover:bg-white/5'
                }`}
              >
                {tier.cta}
              </Link>
            </div>
          ))}
        </div>

        {/* Fine Print */}
        <div className="text-center">
          <p className="text-xs font-mono text-slate-600 leading-relaxed">
            All plans include: 99.9% uptime SLA · Data export · GDPR compliant · SOC 2 in progress
          </p>
        </div>
      </div>

      <style jsx>{`
        @keyframes pulse-glow {
          0%,
          100% {
            box-shadow: 0 0 40px rgba(124, 106, 245, 0.2);
          }
          50% {
            box-shadow: 0 0 60px rgba(124, 106, 245, 0.4);
          }
        }

        .pricing-card-popular {
          animation: pulse-glow 3s ease-in-out infinite;
        }
      `}</style>
    </section>
  );
};

export default PricingSection;
