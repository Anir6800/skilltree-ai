/**
 * HowItWorksSection Component
 * 3-step visual process with animated illustrations and connector lines
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Check, Zap, Trophy, Code } from 'lucide-react';
import useScrollAnimation from '../../hooks/useScrollAnimation';

const HowItWorksSection = () => {
  const { ref, isVisible, className } = useScrollAnimation({ threshold: 0.3 });
  const [step1Complete, setStep1Complete] = useState(false);
  const [treeNodes, setTreeNodes] = useState([]);

  useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => {
        setStep1Complete(true);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [isVisible]);

  useEffect(() => {
    if (isVisible) {
      const nodes = [
        { id: 1, delay: 0 },
        { id: 2, delay: 300 },
        { id: 3, delay: 600 },
        { id: 4, delay: 900 },
        { id: 5, delay: 1200 },
      ];

      nodes.forEach((node) => {
        setTimeout(() => {
          setTreeNodes((prev) => [...prev, node.id]);
        }, node.delay);
      });
    }
  }, [isVisible]);

  return (
    <section
      id="how-it-works"
      ref={ref}
      className={`relative py-24 px-6 bg-gradient-to-b from-[#0a0c10] to-[#0f1117] ${className} animate-in-default`}
    >
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-20">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm mb-4">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              ✦ THE PROCESS
            </span>
          </div>
          <h2 className="text-5xl font-black tracking-tighter mb-4 text-white">
            From zero to job-ready in 3 steps
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            No guesswork. No generic content. A path built by AI around your exact situation.
          </p>
        </div>

        {/* Timeline */}
        <div className="relative">
          {/* Desktop Connector Line */}
          <div className="hidden lg:block absolute top-32 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-purple-500/30 to-transparent">
            <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
              <line
                x1="16.66%"
                y1="0"
                x2="83.33%"
                y2="0"
                stroke="url(#gradient)"
                strokeWidth="2"
                strokeDasharray="8,8"
                className={isVisible ? 'animate-draw-line' : ''}
              />
              <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#7c6af5" stopOpacity="0.5" />
                  <stop offset="50%" stopColor="#38d9d9" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#3dd68c" stopOpacity="0.5" />
                </linearGradient>
              </defs>
            </svg>
          </div>

          {/* Steps Grid */}
          <div className="grid lg:grid-cols-3 gap-12 lg:gap-8">
            {/* Step 1 */}
            <div className="relative">
              <div className="flex flex-col items-center text-center">
                {/* Step Number */}
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-600 to-purple-800 flex items-center justify-center text-2xl font-black text-white mb-6 shadow-[0_0_30px_rgba(124,106,245,0.4)] relative z-10">
                  01
                </div>

                {/* Illustration */}
                <div className="w-full h-48 mb-6 bg-white/5 border border-white/10 rounded-2xl p-6 flex items-center justify-center overflow-hidden relative">
                  <div className="relative w-full h-full">
                    {/* Form/Quiz Card */}
                    <div className="absolute inset-0 flex flex-col space-y-3">
                      <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 rounded-full bg-purple-500" />
                        <div className="flex-1 h-2 bg-white/10 rounded" />
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 rounded-full bg-purple-500" />
                        <div className="flex-1 h-2 bg-white/10 rounded" />
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 rounded-full bg-purple-500" />
                        <div className="flex-1 h-2 bg-white/10 rounded" />
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full transition-all duration-500 ${step1Complete ? 'bg-green-500' : 'bg-white/20'}`} />
                        <div className="flex-1 h-2 bg-white/10 rounded" />
                      </div>
                    </div>

                    {/* Animated Checkmark */}
                    {step1Complete && (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-16 h-16 rounded-full bg-green-500/20 border-2 border-green-500 flex items-center justify-center animate-scale-in">
                          <Check size={32} className="text-green-500" />
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Content */}
                <div className="mb-4">
                  <div className="inline-flex items-center px-3 py-1 bg-purple-500/20 border border-purple-500/30 rounded-full mb-3">
                    <span className="text-xs font-semibold text-purple-300">Takes 2 minutes</span>
                  </div>
                  <h3 className="text-xl font-black text-white mb-3">Share your goals & gaps</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">
                    Answer 6 quick questions: your target role, current knowledge level per category, and how many hours per week you can commit.
                  </p>
                </div>
              </div>
            </div>

            {/* Step 2 */}
            <div className="relative">
              <div className="flex flex-col items-center text-center">
                {/* Step Number */}
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-600 to-cyan-800 flex items-center justify-center text-2xl font-black text-white mb-6 shadow-[0_0_30px_rgba(56,217,217,0.4)] relative z-10">
                  02
                </div>

                {/* Illustration */}
                <div className="w-full h-48 mb-6 bg-white/5 border border-white/10 rounded-2xl p-6 flex items-center justify-center overflow-hidden relative">
                  <svg viewBox="0 0 200 150" className="w-full h-full">
                    {/* Tree Structure */}
                    <g>
                      {/* Connections */}
                      {treeNodes.includes(2) && (
                        <line x1="100" y1="30" x2="70" y2="70" stroke="#7c6af5" strokeWidth="2" opacity="0.5" />
                      )}
                      {treeNodes.includes(3) && (
                        <line x1="100" y1="30" x2="130" y2="70" stroke="#7c6af5" strokeWidth="2" opacity="0.5" />
                      )}
                      {treeNodes.includes(4) && (
                        <line x1="70" y1="70" x2="50" y2="110" stroke="#38d9d9" strokeWidth="2" opacity="0.5" />
                      )}
                      {treeNodes.includes(5) && (
                        <line x1="130" y1="70" x2="150" y2="110" stroke="#3dd68c" strokeWidth="2" opacity="0.5" />
                      )}

                      {/* Nodes */}
                      {treeNodes.includes(1) && (
                        <g className="animate-scale-in">
                          <circle cx="100" cy="30" r="12" fill="#7c6af5" opacity="0.3" />
                          <circle cx="100" cy="30" r="8" fill="#7c6af5" />
                        </g>
                      )}
                      {treeNodes.includes(2) && (
                        <g className="animate-scale-in">
                          <circle cx="70" cy="70" r="12" fill="#7c6af5" opacity="0.3" />
                          <circle cx="70" cy="70" r="8" fill="#7c6af5" />
                        </g>
                      )}
                      {treeNodes.includes(3) && (
                        <g className="animate-scale-in">
                          <circle cx="130" cy="70" r="12" fill="#7c6af5" opacity="0.3" />
                          <circle cx="130" cy="70" r="8" fill="#7c6af5" />
                        </g>
                      )}
                      {treeNodes.includes(4) && (
                        <g className="animate-scale-in">
                          <circle cx="50" cy="110" r="12" fill="#38d9d9" opacity="0.3" />
                          <circle cx="50" cy="110" r="8" fill="#38d9d9" />
                        </g>
                      )}
                      {treeNodes.includes(5) && (
                        <g className="animate-scale-in">
                          <circle cx="150" cy="110" r="12" fill="#3dd68c" opacity="0.3" />
                          <circle cx="150" cy="110" r="8" fill="#3dd68c" />
                        </g>
                      )}
                    </g>
                  </svg>
                </div>

                {/* Content */}
                <div className="mb-4">
                  <div className="inline-flex items-center px-3 py-1 bg-cyan-500/20 border border-cyan-500/30 rounded-full mb-3">
                    <span className="text-xs font-semibold text-cyan-300">Instant generation</span>
                  </div>
                  <h3 className="text-xl font-black text-white mb-3">Get your personal skill tree</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">
                    Our AI analyzes your profile, maps your existing knowledge, skips what you already know, and surfaces the exact 10 skills to tackle first.
                  </p>
                </div>
              </div>
            </div>

            {/* Step 3 */}
            <div className="relative">
              <div className="flex flex-col items-center text-center">
                {/* Step Number */}
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-green-600 to-green-800 flex items-center justify-center text-2xl font-black text-white mb-6 shadow-[0_0_30px_rgba(61,214,140,0.4)] relative z-10">
                  03
                </div>

                {/* Illustration */}
                <div className="w-full h-48 mb-6 bg-white/5 border border-white/10 rounded-2xl p-6 flex flex-col justify-between overflow-hidden relative">
                  {/* Code Editor Mockup */}
                  <div className="bg-black/50 rounded-lg p-2 border border-white/5 flex-1 mb-2">
                    <div className="flex items-center space-x-1 mb-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
                      <div className="w-1.5 h-1.5 rounded-full bg-yellow-500" />
                      <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                    </div>
                    <div className="space-y-1">
                      <div className="h-1 bg-purple-500/30 rounded w-3/4" />
                      <div className="h-1 bg-cyan-500/30 rounded w-1/2" />
                      <div className="h-1 bg-green-500/30 rounded w-2/3" />
                    </div>
                  </div>

                  {/* XP Bar */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-slate-500 font-semibold">XP</span>
                      <span className="text-green-400 font-bold">+250</span>
                    </div>
                    <div className="h-2 bg-black/30 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full animate-xp-fill" />
                    </div>
                  </div>

                  {/* Trophy */}
                  <div className="absolute top-2 right-2">
                    <Trophy size={24} className="text-yellow-500 animate-bounce-slow" />
                  </div>
                </div>

                {/* Content */}
                <div className="mb-4">
                  <div className="inline-flex items-center px-3 py-1 bg-green-500/20 border border-green-500/30 rounded-full mb-3">
                    <span className="text-xs font-semibold text-green-300">Gamified & addictive</span>
                  </div>
                  <h3 className="text-xl font-black text-white mb-3">Code, compete, and level up</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">
                    Complete AI-validated quests, race other developers, and watch your skill tree expand. Every quest you pass unlocks the next skill.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="text-center mt-16">
          <p className="text-lg text-slate-400 mb-6">Ready to start?</p>
          <Link
            to="/register"
            className="inline-flex items-center space-x-2 px-8 py-4 bg-gradient-to-r from-purple-600 via-cyan-600 to-green-600 text-white font-bold text-lg rounded-lg hover:shadow-[0_0_40px_rgba(124,106,245,0.5)] transition-all"
          >
            <Zap size={20} fill="white" />
            <span>Create My Skill Tree →</span>
          </Link>
        </div>
      </div>

      <style jsx>{`
        @keyframes draw-line {
          from {
            stroke-dashoffset: 1000;
          }
          to {
            stroke-dashoffset: 0;
          }
        }

        .animate-draw-line {
          stroke-dasharray: 1000;
          animation: draw-line 2s ease-out forwards;
        }

        @keyframes scale-in {
          from {
            transform: scale(0);
            opacity: 0;
          }
          to {
            transform: scale(1);
            opacity: 1;
          }
        }

        .animate-scale-in {
          animation: scale-in 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        @keyframes xp-fill {
          from {
            width: 0%;
          }
          to {
            width: 75%;
          }
        }

        .animate-xp-fill {
          animation: xp-fill 1.5s ease-out forwards;
        }

        @keyframes bounce-slow {
          0%,
          100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-8px);
          }
        }

        .animate-bounce-slow {
          animation: bounce-slow 2s ease-in-out infinite;
        }
      `}</style>
    </section>
  );
};

export default HowItWorksSection;
