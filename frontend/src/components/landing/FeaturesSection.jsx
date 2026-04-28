/**
 * FeaturesSection Component
 * Bento-grid feature showcase with animated mockups and hover effects
 */

import React, { useState, useEffect } from 'react';
import { Terminal, Zap, Swords, Bot, Trophy, Shield } from 'lucide-react';
import useScrollAnimation from '../../hooks/useScrollAnimation';

const FeaturesSection = () => {
  const { ref, className } = useScrollAnimation({ threshold: 0.2 });
  const [terminalText, setTerminalText] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  const codeToType = `def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1`;

  useEffect(() => {
    if (terminalText.length < codeToType.length) {
      const timeout = setTimeout(() => {
        setTerminalText(codeToType.slice(0, terminalText.length + 1));
      }, 30);
      return () => clearTimeout(timeout);
    } else if (!showSuccess) {
      const timeout = setTimeout(() => {
        setShowSuccess(true);
      }, 500);
      return () => clearTimeout(timeout);
    }
  }, [terminalText, showSuccess, codeToType]);

  useEffect(() => {
    const timeout1 = setTimeout(() => {
      setChatMessages([{ type: 'user', text: 'Why is my solution O(n²)?' }]);
    }, 1000);

    const timeout2 = setTimeout(() => {
      setIsTyping(true);
    }, 2000);

    const timeout3 = setTimeout(() => {
      setIsTyping(false);
      setChatMessages((prev) => [
        ...prev,
        {
          type: 'ai',
          text: 'Your nested loops iterate through the array twice. Consider using a hash map to achieve O(n) time complexity.',
        },
      ]);
    }, 3500);

    return () => {
      clearTimeout(timeout1);
      clearTimeout(timeout2);
      clearTimeout(timeout3);
    };
  }, []);

  const [leaderboard] = useState([
    { rank: 1, name: 'alex_dev', xp: 12450, change: 'up' },
    { rank: 2, name: 'sarah_codes', xp: 11890, change: 'up' },
    { rank: 3, name: 'mike_algo', xp: 10320, change: 'down' },
  ]);

  const [skillNodes] = useState([
    { x: 20, y: 30, size: 8, color: '#7c6af5', delay: 0 },
    { x: 50, y: 20, size: 10, color: '#38d9d9', delay: 0.5 },
    { x: 80, y: 35, size: 7, color: '#3dd68c', delay: 1 },
    { x: 35, y: 60, size: 9, color: '#7c6af5', delay: 1.5 },
    { x: 65, y: 55, size: 8, color: '#38d9d9', delay: 2 },
  ]);

  return (
    <section
      id="features"
      ref={ref}
      className={`relative py-24 px-6 bg-[#0a0c10] ${className} animate-in-default`}
    >
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm mb-4">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              ✦ EVERYTHING YOU NEED
            </span>
          </div>
          <h2 className="text-5xl font-black tracking-tighter mb-4 text-white">
            The full stack of developer growth tools
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            Built for the way developers actually learn — by doing, competing, and getting precise AI feedback.
          </p>
        </div>

        {/* Bento Grid */}
        <div className="bento-features-grid gap-3">
          {/* Cell A - AI Skill Mapping (Large 2x2) */}
          <div className="bento-cell cell-a group">
            <div className="relative h-full flex flex-col justify-between p-8 bg-gradient-to-br from-purple-900/20 to-transparent border-2 border-purple-500/30 rounded-2xl overflow-hidden transition-all duration-300 hover:border-purple-500 hover:shadow-[0_0_40px_rgba(124,106,245,0.3)]">
              {/* Animated Skill Tree Background */}
              <div className="absolute inset-0 overflow-hidden opacity-40">
                <svg className="w-full h-full">
                  {skillNodes.map((node, idx) => (
                    <g key={idx}>
                      <circle
                        cx={`${node.x}%`}
                        cy={`${node.y}%`}
                        r={node.size}
                        fill={node.color}
                        className="animate-pulse-slow"
                        style={{ animationDelay: `${node.delay}s` }}
                      />
                      {idx < skillNodes.length - 1 && (
                        <line
                          x1={`${node.x}%`}
                          y1={`${node.y}%`}
                          x2={`${skillNodes[idx + 1].x}%`}
                          y2={`${skillNodes[idx + 1].y}%`}
                          stroke={node.color}
                          strokeWidth="1"
                          strokeOpacity="0.3"
                          strokeDasharray="4,4"
                        />
                      )}
                    </g>
                  ))}
                </svg>
              </div>

              <div className="relative z-10">
                <div className="w-16 h-16 mb-4 transition-transform duration-300 group-hover:-translate-y-1">
                  <Zap size={48} className="text-purple-400" />
                </div>
                <h3 className="text-2xl font-black text-white mb-3">AI Skill Tree</h3>
                <p className="text-slate-300 leading-relaxed">
                  Your personalized DAG of skills, dependencies, and unlocks — built by AI from your goals.
                </p>
              </div>

              <div className="relative z-10 mt-4">
                <div className="inline-flex items-center space-x-2 px-3 py-1 bg-purple-500/20 border border-purple-500/30 rounded-full">
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" />
                  <span className="text-xs font-semibold text-purple-300">Adaptive Learning</span>
                </div>
              </div>
            </div>
          </div>

          {/* Cell B - Code Execution */}
          <div className="bento-cell cell-b group">
            <div className="h-full flex flex-col justify-between p-6 bg-gradient-to-br from-slate-900/50 to-transparent border-2 border-slate-700/30 rounded-2xl overflow-hidden transition-all duration-300 hover:border-cyan-500 hover:shadow-[0_0_40px_rgba(56,217,217,0.2)]">
              <div>
                <div className="flex items-center space-x-2 mb-4">
                  <Terminal size={24} className="text-cyan-400 transition-transform duration-300 group-hover:-translate-y-1" />
                  <h3 className="text-lg font-black text-white">5-Language Sandbox</h3>
                </div>
                <p className="text-sm text-slate-400 mb-4">
                  Write Python, JS, C++, Java, or Go. Compiled in an isolated container. Zero setup.
                </p>
              </div>

              <div className="bg-black/50 rounded-lg p-3 border border-white/5">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 rounded-full bg-red-500" />
                    <div className="w-2 h-2 rounded-full bg-yellow-500" />
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                  </div>
                  <span className="text-xs text-slate-500 font-mono">main.py</span>
                </div>
                <pre className="text-xs font-mono text-green-400 h-24 overflow-hidden">
                  {terminalText}
                  <span className="inline-block w-1 h-3 bg-green-400 ml-0.5 animate-blink" />
                </pre>
                {showSuccess && (
                  <div className="mt-2 text-xs font-mono text-green-400 animate-in-default animate-in">
                    ✓ All tests passed
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Cell C - Multiplayer Arena */}
          <div className="bento-cell cell-c group">
            <div className="h-full flex flex-col justify-between p-6 bg-gradient-to-br from-red-900/20 via-amber-900/20 to-transparent border-2 border-amber-700/30 rounded-2xl overflow-hidden transition-all duration-300 hover:border-amber-500 hover:shadow-[0_0_40px_rgba(251,191,36,0.2)]">
              <div>
                <div className="flex items-center space-x-2 mb-4">
                  <span className="text-2xl transition-transform duration-300 group-hover:-translate-y-1">⚔️</span>
                  <h3 className="text-lg font-black text-white">Live Coding Races</h3>
                </div>
                <p className="text-sm text-slate-400 mb-4">
                  Challenge other developers in real-time. First to solve all tests wins XP.
                </p>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-pink-500" />
                    <span className="text-xs font-semibold text-white">You</span>
                  </div>
                  <span className="text-xs font-mono text-amber-400">2/3</span>
                </div>
                <div className="w-full h-2 bg-black/30 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full animate-progress-66" />
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500" />
                    <span className="text-xs font-semibold text-white">Opponent</span>
                  </div>
                  <span className="text-xs font-mono text-amber-400">1/3</span>
                </div>
                <div className="w-full h-2 bg-black/30 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full animate-progress-33" />
                </div>
              </div>
            </div>
          </div>

          {/* Cell D - AI Mentor */}
          <div className="bento-cell cell-d group">
            <div className="h-full flex flex-col justify-between p-6 bg-gradient-to-br from-blue-900/20 to-transparent border-2 border-blue-700/30 rounded-2xl overflow-hidden transition-all duration-300 hover:border-blue-500 hover:shadow-[0_0_40px_rgba(59,130,246,0.2)]">
              <div>
                <div className="flex items-center space-x-2 mb-4">
                  <span className="text-2xl transition-transform duration-300 group-hover:-translate-y-1">🤖</span>
                  <h3 className="text-lg font-black text-white">AI Code Mentor</h3>
                </div>
                <p className="text-sm text-slate-400 mb-4">
                  Ask anything. Get context-aware guidance powered by RAG and your skill history.
                </p>
              </div>

              <div className="space-y-2">
                {chatMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg text-xs ${
                      msg.type === 'user'
                        ? 'bg-purple-500/20 border border-purple-500/30 text-white ml-4'
                        : 'bg-blue-500/20 border border-blue-500/30 text-slate-200 mr-4'
                    }`}
                  >
                    {msg.text}
                  </div>
                ))}
                {isTyping && (
                  <div className="flex items-center space-x-1 p-3 bg-blue-500/20 border border-blue-500/30 rounded-lg mr-4">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Cell E - Leaderboard */}
          <div className="bento-cell cell-e group">
            <div className="h-full flex flex-col justify-between p-6 bg-gradient-to-br from-yellow-900/20 to-transparent border-2 border-yellow-700/30 rounded-2xl overflow-hidden transition-all duration-300 hover:border-yellow-500 hover:shadow-[0_0_40px_rgba(234,179,8,0.2)]">
              <div>
                <div className="flex items-center space-x-2 mb-4">
                  <span className="text-2xl transition-transform duration-300 group-hover:-translate-y-1">🏆</span>
                  <h3 className="text-lg font-black text-white">Global Leaderboard</h3>
                </div>
                <p className="text-sm text-slate-400 mb-4">
                  Compete globally or with friends. Weekly resets keep it fresh.
                </p>
              </div>

              <div className="space-y-2">
                {leaderboard.map((entry) => (
                  <div
                    key={entry.rank}
                    className="flex items-center justify-between p-2 bg-black/30 rounded-lg border border-white/5"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-6 h-6 flex items-center justify-center bg-yellow-500/20 rounded text-xs font-bold text-yellow-400">
                        {entry.rank}
                      </div>
                      <span className="text-xs font-semibold text-white">{entry.name}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono text-slate-400">{entry.xp.toLocaleString()}</span>
                      <span className={entry.change === 'up' ? 'text-green-400' : 'text-red-400'}>
                        {entry.change === 'up' ? '↑' : '↓'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Cell F - Full-width Promo Strip */}
          <div className="bento-cell cell-f group">
            <div className="h-full flex items-center justify-center p-6 bg-gradient-to-r from-amber-900/20 via-orange-900/20 to-amber-900/20 border-2 border-amber-700/30 rounded-2xl overflow-hidden transition-all duration-300 hover:border-amber-500 hover:shadow-[0_0_40px_rgba(251,191,36,0.2)]">
              <div className="overflow-hidden whitespace-nowrap">
                <div className="inline-block animate-scroll-text">
                  <span className="text-sm font-mono text-amber-400 mx-8">
                    Also includes: AI Plagiarism Detection · Personalized Weekly Curriculum · Admin Content Engine · 180+ Quests · Achievement Badges · Code Style Coach · Peer Review System
                  </span>
                  <span className="text-sm font-mono text-amber-400 mx-8">
                    Also includes: AI Plagiarism Detection · Personalized Weekly Curriculum · Admin Content Engine · 180+ Quests · Achievement Badges · Code Style Coach · Peer Review System
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .bento-features-grid {
          display: grid;
          grid-template-areas:
            'a a b c'
            'a a d e'
            'f f f f';
          grid-template-columns: repeat(4, 1fr);
          grid-template-rows: repeat(3, minmax(200px, auto));
        }

        .cell-a {
          grid-area: a;
        }
        .cell-b {
          grid-area: b;
        }
        .cell-c {
          grid-area: c;
        }
        .cell-d {
          grid-area: d;
        }
        .cell-e {
          grid-area: e;
        }
        .cell-f {
          grid-area: f;
        }

        @media (max-width: 1024px) {
          .bento-features-grid {
            grid-template-areas:
              'a a'
              'a a'
              'b c'
              'd e'
              'f f';
            grid-template-columns: repeat(2, 1fr);
            grid-template-rows: repeat(5, minmax(200px, auto));
          }
        }

        @media (max-width: 640px) {
          .bento-features-grid {
            grid-template-areas:
              'a'
              'b'
              'c'
              'd'
              'e'
              'f';
            grid-template-columns: 1fr;
            grid-template-rows: repeat(6, minmax(200px, auto));
          }
        }

        @keyframes pulse-slow {
          0%,
          100% {
            opacity: 0.6;
            transform: scale(1);
          }
          50% {
            opacity: 1;
            transform: scale(1.1);
          }
        }

        .animate-pulse-slow {
          animation: pulse-slow 3s ease-in-out infinite;
        }

        @keyframes blink {
          0%,
          50% {
            opacity: 1;
          }
          51%,
          100% {
            opacity: 0;
          }
        }

        .animate-blink {
          animation: blink 1s step-start infinite;
        }

        @keyframes progress-66 {
          from {
            width: 0%;
          }
          to {
            width: 66%;
          }
        }

        @keyframes progress-33 {
          from {
            width: 0%;
          }
          to {
            width: 33%;
          }
        }

        .animate-progress-66 {
          animation: progress-66 2s ease-out forwards;
        }

        .animate-progress-33 {
          animation: progress-33 2s ease-out forwards;
        }

        @keyframes scroll-text {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }

        .animate-scroll-text {
          animation: scroll-text 20s linear infinite;
        }
      `}</style>
    </section>
  );
};

export default FeaturesSection;
