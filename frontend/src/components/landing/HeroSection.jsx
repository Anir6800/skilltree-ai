/**
 * HeroSection Component
 * Full-viewport hero with animated particle skill-tree background
 */

import React, { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';

class Particle {
  constructor(canvas, colors) {
    this.canvas = canvas;
    this.x = Math.random() * canvas.width;
    this.y = Math.random() * canvas.height;
    this.vx = (Math.random() - 0.5) * 0.3;
    this.vy = (Math.random() - 0.5) * 0.3;
    this.radius = Math.random() * 1.5 + 1;
    this.color = colors[Math.floor(Math.random() * colors.length)];
  }

  update() {
    this.x += this.vx;
    this.y += this.vy;

    if (this.x < 0 || this.x > this.canvas.width) this.vx *= -1;
    if (this.y < 0 || this.y > this.canvas.height) this.vy *= -1;
  }

  draw(ctx) {
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, 0.15)`;
    ctx.fill();
  }
}

const HeroSection = () => {
  const canvasRef = useRef(null);
  const gridCanvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const gridCanvas = gridCanvasRef.current;
    if (!canvas || !gridCanvas) return;

    const ctx = canvas.getContext('2d');
    const gridCtx = gridCanvas.getContext('2d');
    
    const drawGrid = () => {
      gridCtx.clearRect(0, 0, gridCanvas.width, gridCanvas.height);
      gridCtx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
      gridCtx.lineWidth = 1;

      const spacing = 40;

      for (let x = 0; x < gridCanvas.width; x += spacing) {
        gridCtx.beginPath();
        gridCtx.moveTo(x, 0);
        gridCtx.lineTo(x, gridCanvas.height);
        gridCtx.stroke();
      }

      for (let y = 0; y < gridCanvas.height; y += spacing) {
        gridCtx.beginPath();
        gridCtx.moveTo(0, y);
        gridCtx.lineTo(gridCanvas.width, y);
        gridCtx.stroke();
      }
    };

    const setCanvasSize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      gridCanvas.width = window.innerWidth;
      gridCanvas.height = window.innerHeight;
      drawGrid();
    };

    setCanvasSize();

    const particles = [];
    const particleCount = 60;
    const colors = [
      { r: 124, g: 106, b: 245 }, // accent #7c6af5
      { r: 56, g: 217, b: 217 },  // cyan #38d9d9
      { r: 61, g: 214, b: 140 },  // green #3dd68c
    ];

    for (let i = 0; i < particleCount; i++) {
      particles.push(new Particle(canvas, colors));
    }

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach((particle) => {
        particle.update();
        particle.draw(ctx);
      });

      particles.forEach((p1, i) => {
        particles.slice(i + 1).forEach((p2) => {
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < 120) {
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            const opacity = 0.1 * (1 - distance / 120);
            ctx.strokeStyle = `rgba(124, 106, 245, ${opacity})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        });
      });

      requestAnimationFrame(animate);
    };

    animate();

    const handleResize = () => {
      setCanvasSize();
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const skills = [
    { name: 'Two Pointers', category: 'algorithms' },
    { name: 'Dynamic Programming', category: 'algorithms' },
    { name: 'React Hooks', category: 'frontend' },
    { name: 'Neural Networks', category: 'ml' },
    { name: 'System Design', category: 'architecture' },
    { name: 'Dijkstra', category: 'algorithms' },
    { name: 'Binary Search', category: 'algorithms' },
    { name: 'Graph Traversal', category: 'algorithms' },
    { name: 'REST APIs', category: 'backend' },
    { name: 'Docker', category: 'devops' },
    { name: 'SQL Optimization', category: 'database' },
    { name: 'TypeScript', category: 'frontend' },
    { name: 'Microservices', category: 'architecture' },
    { name: 'Redis Caching', category: 'backend' },
  ];

  const getCategoryColor = (category) => {
    const colors = {
      algorithms: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
      frontend: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
      backend: 'bg-green-500/20 text-green-300 border-green-500/30',
      ml: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
      architecture: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
      devops: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
      database: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    };
    return colors[category] || 'bg-slate-500/20 text-slate-300 border-slate-500/30';
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Grid Background */}
      <canvas ref={gridCanvasRef} className="absolute inset-0 pointer-events-none" />

      {/* Animated Particle Background */}
      <canvas ref={canvasRef} className="absolute inset-0 pointer-events-none" />

      {/* Radial Gradient Overlay */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(circle at center, rgba(124, 106, 245, 0.12) 0%, transparent 70%)',
        }}
      />

      {/* Content */}
      <div className="relative z-10 max-w-[860px] mx-auto px-6 text-center pt-32 pb-20">
        {/* Eyebrow Tag */}
        <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm mb-8 animate-in-default animate-in">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            ◉ LIVE — 12,400+ developers learning
          </span>
        </div>

        {/* H1 with Staggered Animation */}
        <h1 className="mb-6">
          <div className="text-[72px] leading-[1.0] font-[800] tracking-[-3px] flex flex-col items-center">
            <span
              className="text-white animate-in-default animate-in"
              style={{ animationDelay: '0ms' }}
            >
              Stop grinding
            </span>
            <span
              className="text-transparent bg-clip-text bg-gradient-to-r from-[#7c6af5] to-[#38d9d9] animate-in-default animate-in"
              style={{ animationDelay: '80ms' }}
            >
              LeetCode
            </span>
            <span
              className="text-white animate-in-default animate-in"
              style={{ animationDelay: '160ms' }}
            >
              blind.
            </span>
          </div>
        </h1>

        {/* Subheadline */}
        <p
          className="text-[18px] text-slate-400 max-w-[520px] mx-auto mb-8 leading-relaxed animate-in-default animate-in"
          style={{ animationDelay: '400ms' }}
        >
          SkillTree AI maps your exact knowledge gaps, builds a custom learning path, and trains you with AI-powered code challenges — until you're actually ready.
        </p>

        {/* CTA Row */}
        <div
          className="flex flex-col sm:flex-row items-center justify-center gap-2 mb-4 animate-in-default animate-in"
          style={{ animationDelay: '600ms' }}
        >
          <Link
            to="/register"
            className="px-8 py-[14px] bg-[#7c6af5] text-white font-semibold text-base rounded-[10px] hover:bg-[#6b59e4] transition-all hover:shadow-[0_0_30px_rgba(124,106,245,0.4)]"
          >
            Start Learning Free →
          </Link>
          <button
            onClick={() => scrollToSection('how-it-works')}
            className="px-8 py-[14px] bg-transparent text-white font-semibold text-base rounded-[10px] border border-white/20 hover:bg-white/5 transition-all"
          >
            See how it works ↓
          </button>
        </div>

        {/* Fine Print */}
        <p
          className="text-xs text-slate-500 mb-12 animate-in-default animate-in"
          style={{ animationDelay: '600ms' }}
        >
          No credit card required · Free forever plan · Cancel anytime
        </p>

        {/* Skill Ticker */}
        <div
          className="relative overflow-hidden py-6 border-t border-b border-white/5 animate-in-default animate-in"
          style={{ animationDelay: '800ms' }}
        >
          <div className="flex animate-ticker">
            {[...skills, ...skills].map((skill, index) => (
              <div
                key={index}
                className={`inline-flex items-center px-4 py-2 mx-2 rounded-lg border text-xs font-medium whitespace-nowrap ${getCategoryColor(
                  skill.category
                )}`}
              >
                {skill.name}
              </div>
            ))}
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes ticker {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }

        .animate-ticker {
          animation: ticker 40s linear infinite;
        }

        .animate-ticker:hover {
          animation-play-state: paused;
        }
      `}</style>
    </section>
  );
};

export default HeroSection;
