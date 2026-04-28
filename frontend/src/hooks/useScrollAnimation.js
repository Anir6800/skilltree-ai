/**
 * useScrollAnimation Hook
 * Provides IntersectionObserver-based scroll animations with stagger support
 * @module hooks/useScrollAnimation
 */

import { useEffect, useRef, useState } from 'react';

/**
 * Custom hook for scroll-triggered animations
 * @param {Object} options - Configuration options
 * @param {number} [options.delay=0] - Delay in milliseconds before animation starts
 * @param {number} [options.threshold=0.1] - Intersection threshold (0-1)
 * @param {boolean} [options.once=true] - Whether to animate only once
 * @returns {Object} - { ref, isVisible, className }
 */
export const useScrollAnimation = ({ delay = 0, threshold = 0.1, once = true } = {}) => {
  const ref = useRef(null);
  const [isVisible, setIsVisible] = useState(false);
  const [hasAnimated, setHasAnimated] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    // If already animated and once is true, skip
    if (once && hasAnimated) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          // Apply delay if specified
          if (delay > 0) {
            setTimeout(() => {
              setIsVisible(true);
              setHasAnimated(true);
            }, delay);
          } else {
            setIsVisible(true);
            setHasAnimated(true);
          }

          // Disconnect if once is true
          if (once) {
            observer.disconnect();
          }
        } else if (!once) {
          setIsVisible(false);
        }
      },
      {
        threshold,
        rootMargin: '0px 0px -50px 0px',
      }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [delay, threshold, once, hasAnimated]);

  return {
    ref,
    isVisible,
    className: isVisible ? 'animate-in' : '',
  };
};

export default useScrollAnimation;
