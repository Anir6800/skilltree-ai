/**
 * SnakeGame — offline canvas snake for the generation loading screen.
 * Arrow keys / WASD to steer, Space to start or restart. No dependencies.
 */

import { useEffect, useRef } from 'react';

const N = 20;          // grid cells per side
const CELL = 16;
const SIZE = N * CELL;

export default function SnakeGame() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    const g = {
      state: 'idle', // idle | run | over
      snake: [],
      dir: { x: 1, y: 0 },
      nextDir: { x: 1, y: 0 },
      food: { x: 14, y: 10 },
      score: 0,
      hi: Number(localStorage.getItem('snake_hi') || 0),
      acc: 0,
    };

    const placeFood = () => {
      do {
        g.food = { x: Math.floor(Math.random() * N), y: Math.floor(Math.random() * N) };
      } while (g.snake.some((s) => s.x === g.food.x && s.y === g.food.y));
    };

    const reset = () => {
      g.snake = [{ x: 6, y: 10 }, { x: 5, y: 10 }, { x: 4, y: 10 }];
      g.dir = { x: 1, y: 0 };
      g.nextDir = { x: 1, y: 0 };
      g.score = 0;
      g.acc = 0;
      placeFood();
    };

    const start = () => {
      if (g.state !== 'run') {
        reset();
        g.state = 'run';
      }
    };

    const onKey = (e) => {
      const dirs = {
        ArrowUp: { x: 0, y: -1 }, KeyW: { x: 0, y: -1 },
        ArrowDown: { x: 0, y: 1 }, KeyS: { x: 0, y: 1 },
        ArrowLeft: { x: -1, y: 0 }, KeyA: { x: -1, y: 0 },
        ArrowRight: { x: 1, y: 0 }, KeyD: { x: 1, y: 0 },
      };
      if (e.code === 'Space') {
        e.preventDefault();
        start();
        return;
      }
      const d = dirs[e.code];
      if (!d) return;
      e.preventDefault();
      if (g.state !== 'run') start();
      // no reversing into yourself
      if (d.x !== -g.dir.x || d.y !== -g.dir.y) g.nextDir = d;
    };
    window.addEventListener('keydown', onKey);
    canvas.addEventListener('pointerdown', start);

    const tick = () => {
      g.dir = g.nextDir;
      const head = { x: g.snake[0].x + g.dir.x, y: g.snake[0].y + g.dir.y };

      const hitWall = head.x < 0 || head.y < 0 || head.x >= N || head.y >= N;
      const hitSelf = g.snake.some((s) => s.x === head.x && s.y === head.y);
      if (hitWall || hitSelf) {
        g.state = 'over';
        g.hi = Math.max(g.hi, g.score);
        localStorage.setItem('snake_hi', String(g.hi));
        return;
      }

      g.snake.unshift(head);
      if (head.x === g.food.x && head.y === g.food.y) {
        g.score += 1;
        placeFood();
      } else {
        g.snake.pop();
      }
    };

    let last = 0;
    let raf;
    const step = (ts) => {
      if (g.state === 'run') {
        g.acc += last ? ts - last : 0;
        const tickMs = Math.max(70, 140 - g.score * 3); // speeds up gently
        while (g.acc >= tickMs && g.state === 'run') {
          g.acc -= tickMs;
          tick();
        }
      }
      last = ts;

      // ── draw ──
      ctx.fillStyle = '#0a0a0a';
      ctx.fillRect(0, 0, SIZE, SIZE);

      ctx.fillStyle = '#ef4444';
      ctx.beginPath();
      ctx.arc(g.food.x * CELL + CELL / 2, g.food.y * CELL + CELL / 2, CELL / 2 - 3, 0, Math.PI * 2);
      ctx.fill();

      g.snake.forEach((s, i) => {
        ctx.fillStyle = i === 0 ? '#f87171' : '#64748b';
        ctx.beginPath();
        ctx.roundRect(s.x * CELL + 1, s.y * CELL + 1, CELL - 2, CELL - 2, 4);
        ctx.fill();
      });

      ctx.fillStyle = '#94a3b8';
      ctx.font = 'bold 13px monospace';
      ctx.textAlign = 'right';
      ctx.fillText(`HI ${g.hi}  ${g.score}`, SIZE - 10, 20);

      if (g.state !== 'run') {
        ctx.fillStyle = '#e2e8f0';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(
          g.state === 'idle' ? 'PRESS SPACE OR TAP TO PLAY' : 'GAME OVER — SPACE TO RESTART',
          SIZE / 2, SIZE / 2 - 6,
        );
      }

      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('keydown', onKey);
      canvas.removeEventListener('pointerdown', start);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      width={SIZE}
      height={SIZE}
      className="w-full max-w-[320px] mx-auto rounded-2xl border border-white/10 bg-[#0a0a0a] cursor-pointer select-none"
      aria-label="Snake mini-game"
    />
  );
}
