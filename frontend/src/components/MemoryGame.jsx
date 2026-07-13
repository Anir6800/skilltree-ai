/**
 * MemoryGame — flip-and-match pairs for the generation loading screen.
 * Pure React state, no dependencies.
 */

import { useState } from 'react';
import { cn } from '../utils/cn';

const EMOJIS = ['🚀', '🔥', '⚡', '🎯', '🧠', '💎', '🐍', '🌟'];

function freshDeck() {
  return [...EMOJIS, ...EMOJIS]
    .map((emoji) => ({ emoji, key: Math.random() }))
    .sort((a, b) => a.key - b.key)
    .map((c, id) => ({ id, emoji: c.emoji, flipped: false, matched: false }));
}

export default function MemoryGame() {
  const [cards, setCards] = useState(freshDeck);
  const [picked, setPicked] = useState([]); // ids of currently flipped, unmatched cards
  const [moves, setMoves] = useState(0);
  const won = cards.every((c) => c.matched);

  const flip = (id) => {
    const card = cards.find((c) => c.id === id);
    if (picked.length === 2 || card.flipped || card.matched) return;

    const next = cards.map((c) => (c.id === id ? { ...c, flipped: true } : c));
    const nowPicked = [...picked, id];
    setCards(next);
    setPicked(nowPicked);

    if (nowPicked.length === 2) {
      setMoves((m) => m + 1);
      const [a, b] = nowPicked.map((i) => next.find((c) => c.id === i));
      if (a.emoji === b.emoji) {
        setCards(next.map((c) =>
          nowPicked.includes(c.id) ? { ...c, matched: true } : c
        ));
        setPicked([]);
      } else {
        setTimeout(() => {
          setCards((cur) => cur.map((c) =>
            nowPicked.includes(c.id) ? { ...c, flipped: false } : c
          ));
          setPicked([]);
        }, 700);
      }
    }
  };

  const restart = () => {
    setCards(freshDeck());
    setPicked([]);
    setMoves(0);
  };

  return (
    <div className="w-full max-w-[320px] mx-auto select-none">
      <div className="flex items-center justify-between mb-2 text-xs font-bold font-mono text-slate-400">
        <span>MOVES {moves}</span>
        {won && <span className="text-red-400">CLEARED! 🎉</span>}
        <button onClick={restart} className="text-slate-500 hover:text-red-400 transition-colors uppercase">
          Restart
        </button>
      </div>
      <div className="grid grid-cols-4 gap-2">
        {cards.map((card) => (
          <button
            key={card.id}
            onClick={() => flip(card.id)}
            className={cn(
              'h-16 rounded-xl border text-2xl transition-all duration-200',
              card.matched
                ? 'bg-red-500/15 border-red-500/40'
                : card.flipped
                  ? 'bg-white/10 border-white/20'
                  : 'bg-white/5 border-white/10 hover:border-red-500/30 hover:bg-white/10'
            )}
            aria-label={card.flipped || card.matched ? card.emoji : 'hidden card'}
          >
            {card.flipped || card.matched ? card.emoji : <span className="text-slate-600 text-lg">?</span>}
          </button>
        ))}
      </div>
    </div>
  );
}
