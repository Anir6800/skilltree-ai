import { useState } from 'react'
import logo from './assets/logo.png'
import './App.css'

function App() {
  return (
    <div className="app-container">
      {/* Header */}
      <header className="glass-panel main-header">
        <div className="header-content">
          <div className="brand">
            <img src={logo} className="header-logo" alt="SkillTree AI Logo" />
            <span className="brand-name">SkillTree <span className="premium-gradient-text">AI</span></span>
          </div>
          <nav className="header-nav">
            <a href="#features">Features</a>
            <a href="#nodes">Nodes</a>
            <a href="#about">About</a>
            <button className="cta-button-small">Launch Console</button>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <main className="hero-section">
        <div className="hero-content">
          <div className="logo-container floating">
            <img src={logo} className="hero-logo" alt="SkillTree AI" />
          </div>
          <h1 className="hero-title">
            Master the <br />
            <span className="premium-gradient-text">Neural Skill Graph</span>
          </h1>
          <p className="hero-subtitle">
            The immersive AI-driven platform for visual progression and real-time skill acquisition.
          </p>
          <div className="hero-actions">
            <button className="primary-cta">Get Started Free</button>
            <button className="secondary-cta glass-panel">Explore Tree</button>
          </div>
        </div>
      </main>

      {/* Stats / Floating Panels */}
      <section className="stats-grid">
        <div className="glass-panel stat-card">
          <div className="stat-value">12.4k</div>
          <div className="stat-label">Nodes Created</div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-value">98%</div>
          <div className="stat-label">AI Accuracy</div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-value">2.5s</div>
          <div className="stat-label">Sync Latency</div>
        </div>
      </section>
    </div>
  )
}

export default App
