/**
 * useMagneticHover Hook
 * Subtly pulls an element toward the cursor on hover for a tactile micro-interaction
 * @module hooks/useMagneticHover
 */

import { useRef } from 'react';

export const useMagneticHover = (strength = 0.3) => {
  const ref = useRef(null);

  const onMouseMove = (e) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = e.clientX - (rect.left + rect.width / 2);
    const y = e.clientY - (rect.top + rect.height / 2);
    el.style.transform = `translate(${x * strength}px, ${y * strength}px)`;
  };

  const onMouseLeave = () => {
    const el = ref.current;
    if (!el) return;
    el.style.transform = 'translate(0px, 0px)';
  };

  return { ref, onMouseMove, onMouseLeave };
};

export default useMagneticHover;
