/**
 * SkillTree AI - Main Layout Wrapper
 * Wraps pages with bottom navigation
 * @module components/layout/MainLayout
 */

import BottomNav from './BottomNav';

/**
 * Main Layout Component
 * Wraps page content and adds bottom navigation
 */
const MainLayout = ({ children, showBottomNav = true }) => {
  return (
    <div className="relative w-full min-h-screen">
      {/* Page content */}
      <div className={showBottomNav ? 'pb-24' : ''}>
        {children}
      </div>

      {/* Bottom navigation */}
      {showBottomNav && <BottomNav />}
    </div>
  );
};

export default MainLayout;
