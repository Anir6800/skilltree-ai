/**
 * DinoGame — offline canvas runner played while the AI generates the roadmap.
 * Space / ArrowUp / tap to jump. Score + local hi-score. No dependencies.
 */

import { useEffect, useRef } from 'react';

const W = 640;
const H = 180;
const GROUND_Y = H - 28;
const GRAVITY = 0.6;
const JUMP_V = -10.5;

export default function DinoGame() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    const g = {
      state: 'idle', // idle | run | over
      dino: { x: 46, y: GROUND_Y, w: 26, h: 34, vy: 0 },
      obstacles: [],
      speed: 4.5,
      frames: 0,
      score: 0,
      hi: Number(localStorage.getItem('dino_hi') || 0),
    };

    const reset = () => {
      g.dino.y = GROUND_Y;
      g.dino.vy = 0;
      g.obstacles = [];
      g.speed = 4.5;
      g.frames = 0;
      g.score = 0;
    };

    const action = () => {
      if (g.state === 'idle') {
        g.state = 'run';
      } else if (g.state === 'over') {
        reset();
        g.state = 'run';
      } else if (g.dino.y >= GROUND_Y) {
        g.dino.vy = JUMP_V;
      }
    };

    const onKey = (e) => {
      if (e.code === 'Space' || e.code === 'ArrowUp') {
        e.preventDefault();
        action();
      }
    };
    window.addEventListener('keydown', onKey);
    canvas.addEventListener('pointerdown', action);

    const spawn = () => {
      const last = g.obstacles[g.obstacles.length - 1];
      const gap = 240 + Math.random() * 220;
      if (!last || last.x < W - gap) {
        const h = 22 + Math.random() * 26;
        g.obstacles.push({ x: W + 10, w: 14 + Math.random() * 12, h });
      }
    };

    // Physics are tuned for 60fps frame-units; dt normalizes them so the game
    // runs at the same speed on 60Hz and 144Hz displays.
    let last = 0;
    const step = (ts) => {
      const dt = last ? Math.min(2.5, (ts - last) / 16.667) : 1;
      last = ts;

      if (g.state === 'run') {
        g.frames += dt;
        g.speed = Math.min(10, g.speed + 0.001 * dt);
        g.score = Math.floor(g.frames / 5);

        g.dino.vy += GRAVITY * dt;
        g.dino.y = Math.min(GROUND_Y, g.dino.y + g.dino.vy * dt);

        spawn();
        g.obstacles.forEach((o) => { o.x -= g.speed * dt; });
        g.obstacles = g.obstacles.filter((o) => o.x + o.w > -10);

        const d = g.dino;
        for (const o of g.obstacles) {
          const hit =
            d.x + d.w - 6 > o.x &&
            d.x + 4 < o.x + o.w &&
            d.y > GROUND_Y - o.h + 4;
          if (hit) {
            g.state = 'over';
            g.hi = Math.max(g.hi, g.score);
            localStorage.setItem('dino_hi', String(g.hi));
            break;
          }
        }
      }

      // ── draw ──
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = '#0a0a0a';
      ctx.fillRect(0, 0, W, H);

      ctx.strokeStyle = '#334155';
      ctx.beginPath();
      ctx.moveTo(0, GROUND_Y + 0.5);
      ctx.lineTo(W, GROUND_Y + 0.5);
      ctx.stroke();

      // dino
      const d = g.dino;
      ctx.fillStyle = '#ef4444';
      ctx.beginPath();
      ctx.roundRect(d.x, d.y - d.h, d.w, d.h, 6);
      ctx.fill();
      ctx.fillStyle = '#0a0a0a';
      ctx.fillRect(d.x + d.w - 9, d.y - d.h + 7, 4, 4); // eye

      // obstacles
      ctx.fillStyle = '#64748b';
      g.obstacles.forEach((o) => {
        ctx.beginPath();
        ctx.roundRect(o.x, GROUND_Y - o.h, o.w, o.h, 3);
        ctx.fill();
      });

      // score
      ctx.fillStyle = '#94a3b8';
      ctx.font = 'bold 13px monospace';
      ctx.textAlign = 'right';
      ctx.fillText(`HI ${g.hi}  ${g.score}`, W - 12, 22);

      if (g.state !== 'run') {
        ctx.fillStyle = '#e2e8f0';
        ctx.font = 'bold 15px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(
          g.state === 'idle' ? 'PRESS SPACE OR TAP TO PLAY' : 'GAME OVER — SPACE TO RESTART',
          W / 2, H / 2 - 8,
        );
      }

      rafRef = requestAnimationFrame(step);
    };

    let rafRef = requestAnimationFrame(step);

    return () => {
      cancelAnimationFrame(rafRef);
      window.removeEventListener('keydown', onKey);
      canvas.removeEventListener('pointerdown', action);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      width={W}
      height={H}
      className="w-full max-w-[640px] rounded-2xl border border-white/10 bg-[#0a0a0a] cursor-pointer select-none"
      aria-label="Dino runner mini-game"
    />
  );
}
