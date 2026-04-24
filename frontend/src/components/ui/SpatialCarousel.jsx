import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const SpatialCarousel = ({ items }) => {
  const [index, setIndex] = useState(0);

  const next = () => setIndex((i) => (i + 1) % items.length);
  const prev = () => setIndex((i) => (i - 1 + items.length) % items.length);

  return (
    <div className="relative w-full h-96 flex items-center justify-center perspective-1000">
      <AnimatePresence mode="popLayout">
        {items.map((item, i) => {
          const offset = i - index;
          const absOffset = Math.abs(offset);
          
          if (absOffset > 2) return null;

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: offset * 200, scale: 0.5, rotateY: offset * 45 }}
              animate={{ 
                opacity: 1 - absOffset * 0.3, 
                x: offset * 150, 
                z: -absOffset * 100,
                scale: 1 - absOffset * 0.1, 
                rotateY: offset * -25,
                zIndex: items.length - absOffset
              }}
              exit={{ opacity: 0, scale: 0.5, x: offset * 200 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="absolute glass-card w-64 h-80 rounded-3xl p-6 flex flex-col justify-between preserve-3d"
            >
              <div className="space-y-4">
                <div className="w-12 h-12 rounded-lg bg-white/10 flex items-center justify-center">
                  {item.icon}
                </div>
                <h3 className="text-xl font-black uppercase tracking-tighter">{item.title}</h3>
                <p className="text-xs text-slate-400 font-light leading-relaxed">{item.description}</p>
              </div>
              
              <div className="pt-4 border-t border-white/5 flex justify-between items-center">
                <span className="text-[10px] font-bold text-primary uppercase">{item.footer}</span>
                <button className="text-[10px] font-bold uppercase tracking-widest text-white hover:text-accent transition-colors">
                  View Case
                </button>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>

      {/* Controls */}
      <div className="absolute bottom-0 flex space-x-4 z-50 pointer-events-auto">
        <button onClick={prev} className="w-10 h-10 rounded-full glass-card flex items-center justify-center hover:bg-white/20 transition-all">
          ←
        </button>
        <button onClick={next} className="w-10 h-10 rounded-full glass-card flex items-center justify-center hover:bg-white/20 transition-all">
          →
        </button>
      </div>
    </div>
  );
};

export default SpatialCarousel;
