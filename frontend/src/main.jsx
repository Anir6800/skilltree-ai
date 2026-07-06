import { StrictMode, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import './index.css'
import router from './router'
import useAuthStore from './store/authStore'
import BadgeNotificationQueue from './components/BadgeNotificationQueue'
import ErrorBoundary from './components/ErrorBoundary'

const App = () => {
  const initialize = useAuthStore(state => state.initialize);

  useEffect(() => {
    initialize();
  }, [initialize]);

  return (
    <ErrorBoundary>
      <RouterProvider router={router} />
      <BadgeNotificationQueue />
    </ErrorBoundary>
  );
};

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
