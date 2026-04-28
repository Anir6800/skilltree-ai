/**
 * TestimonialsSection Component
 * Social proof with featured testimonial cards, quote ticker, and press logos
 */

import React from 'react';
import { Star } from 'lucide-react';
import useScrollAnimation from '../../hooks/useScrollAnimation';

const TestimonialsSection = () => {
  const { ref, className } = useScrollAnimation({ threshold: 0.2 });

  const testimonials = [
    {
      initials: 'SK',
      name: 'Siddharth K.',
      role: 'SDE-2, Google',
      quote: "I'd been trying to crack FAANG for 2 years. SkillTree AI identified that I was weak in Graph algorithms specifically — not all DSA — and fixed that in 3 weeks. Got the Google offer.",
      color: 'from-purple-600 to-purple-800',
    },
    {
      initials: 'AM',
      name: 'Anika M.',
      role: 'Frontend Eng, Stripe',
      quote: "The multiplayer races are insane. Competing against someone solving the same problem live — nothing makes you focus like knowing they're 2 tests ahead of you.",
      color: 'from-cyan-600 to-cyan-800',
    },
    {
      initials: 'RT',
      name: 'Rohan T.',
      role: 'ML Engineer, OpenAI',
      quote: "The AI mentor understands what I've already completed and gives contextual hints. It's like having a senior dev who's read all my code and still has time to answer questions.",
      color: 'from-green-600 to-green-800',
    },
  ];

  const quickQuotes = [
    'Finally a platform that gets it',
    'Better than LeetCode Premium',
    'The AI feedback is scary accurate',
    'Landed my dream job in 8 weeks',
    'Multiplayer mode is addictive',
    'Skill tree visualization is genius',
    'No more tutorial hell',
    'Best $0 I ever spent',
    'Wish this existed 5 years ago',
    'The mentor saved me hours',
    'Gamification actually works',
    'My team uses this for onboarding',
  ];

  const pressLogos = [
    { name: 'TechCrunch', style: 'font-serif font-bold text-2xl' },
    { name: 'Product Hunt', style: 'font-bold text-xl' },
    { name: 'HackerNews', style: 'font-mono text-xl' },
    { name: 'Dev.to', style: 'font-bold text-2xl' },
  ];

  return (
    <section
      id="testimonials"
      ref={ref}
      className={`relative py-24 px-6 bg-[#0a0c10] ${className} animate-in-default`}
    >
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm mb-4">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              ✦ DEVELOPER STORIES
            </span>
          </div>
          <h2 className="text-5xl font-black tracking-tighter mb-4 text-white">
            Real developers. Real results.
          </h2>
          
          {/* Star Rating */}
          <div className="flex items-center justify-center space-x-2 mb-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <Star key={star} size={20} className="text-yellow-500 fill-yellow-500" />
            ))}
          </div>
          <p className="text-sm text-slate-400">
            4.9 average from 800+ reviews
          </p>
        </div>

        {/* Featured Testimonial Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          {testimonials.map((testimonial, index) => (
            <div
              key={index}
              className="testimonial-card group bg-white/5 border border-white/10 rounded-xl p-6 transition-all duration-300 hover:border-purple-500/50 hover:shadow-[0_0_30px_rgba(124,106,245,0.2)] hover:-translate-y-1"
            >
              {/* Avatar */}
              <div className="flex items-start space-x-4 mb-4">
                <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${testimonial.color} flex items-center justify-center text-white font-bold text-sm shadow-lg`}>
                  {testimonial.initials}
                </div>
                <div className="flex-1">
                  <h4 className="text-white font-bold text-sm">{testimonial.name}</h4>
                  <p className="text-slate-400 text-xs">{testimonial.role}</p>
                </div>
              </div>

              {/* Quote */}
              <blockquote className="text-slate-300 text-sm leading-relaxed mb-4 italic">
                "{testimonial.quote}"
              </blockquote>

              {/* Stars */}
              <div className="flex space-x-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <Star key={star} size={14} className="text-yellow-500 fill-yellow-500" />
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Quote Ticker */}
        <div className="mb-16 overflow-hidden py-4 border-t border-b border-white/5">
          <div className="flex animate-quote-ticker-reverse">
            {[...quickQuotes, ...quickQuotes].map((quote, index) => (
              <div
                key={index}
                className="inline-flex items-center px-4 py-2 mx-2 bg-white/5 border border-white/10 rounded-full whitespace-nowrap"
              >
                <span className="text-xs font-mono italic text-slate-400">"{quote}"</span>
              </div>
            ))}
          </div>
        </div>

        {/* Press Strip */}
        <div className="text-center">
          <p className="text-xs uppercase font-semibold text-slate-600 tracking-wider mb-6">
            As featured in
          </p>
          <div className="flex flex-wrap items-center justify-center gap-12">
            {pressLogos.map((logo, index) => (
              <div
                key={index}
                className="text-slate-500 transition-all duration-300 hover:text-white press-logo"
                style={{
                  filter: 'grayscale(1)',
                  opacity: 0.5,
                }}
              >
                <span className={logo.style}>{logo.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes quote-ticker-reverse {
          0% {
            transform: translateX(-50%);
          }
          100% {
            transform: translateX(0);
          }
        }

        .animate-quote-ticker-reverse {
          animation: quote-ticker-reverse 40s linear infinite;
        }

        .animate-quote-ticker-reverse:hover {
          animation-play-state: paused;
        }

        .press-logo:hover {
          filter: grayscale(0) !important;
          opacity: 1 !important;
        }
      `}</style>
    </section>
  );
};

export default TestimonialsSection;
