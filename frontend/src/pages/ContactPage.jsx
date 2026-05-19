import React, { useState } from 'react';
import { Mail, MapPin, MessageSquare, Send, ShieldCheck } from 'lucide-react';
import LandingNav from '../components/landing/LandingNav';
import LandingFooter from '../components/landing/LandingFooter';
import '../styles/landing.css';

const initialForm = {
  name: '',
  email: '',
  subject: '',
  message: '',
};

const ContactPage = () => {
  const [form, setForm] = useState(initialForm);
  const [status, setStatus] = useState({ type: 'idle', message: '' });
  const [submitting, setSubmitting] = useState(false);

  const updateField = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setStatus({ type: 'idle', message: '' });

    try {
      const response = await fetch('/contact-api/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error || 'Unable to send message right now.');
      }

      setForm(initialForm);
      setStatus({ type: 'success', message: 'Message sent. We will get back to you soon.' });
    } catch (error) {
      setStatus({ type: 'error', message: error.message });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0c10] text-white overflow-x-hidden">
      <LandingNav />

      <main className="pt-[60px]">
        <section className="relative border-b border-white/5 overflow-hidden">
          <div className="absolute inset-0 hero-gradient" />
          <div className="relative max-w-7xl mx-auto px-6 py-20 md:py-28 grid lg:grid-cols-[0.85fr_1fr] gap-12">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-purple-500/30 bg-purple-500/10 text-purple-200 text-xs font-bold uppercase tracking-widest mb-6">
                <MessageSquare size={14} />
                Contact
              </div>
              <h1 className="text-5xl md:text-7xl font-black tracking-tighter leading-[0.95] mb-6">
                Tell us what you want to build.
              </h1>
              <p className="text-lg text-slate-300 leading-relaxed max-w-xl mb-10">
                Questions, feedback, partnerships, and support requests all land in the same inbox.
                Send the details and the team will reply directly.
              </p>

              <div className="space-y-4">
                <div className="flex items-center gap-4 text-slate-300">
                  <span className="w-11 h-11 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-purple-300">
                    <Mail size={20} />
                  </span>
                  <span>ishitrathod6@gmail.com</span>
                </div>
                <div className="flex items-center gap-4 text-slate-300">
                  <span className="w-11 h-11 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-purple-300">
                    <MapPin size={20} />
                  </span>
                  <span>Remote support for SkillTree.AI users</span>
                </div>
                <div className="flex items-center gap-4 text-slate-300">
                  <span className="w-11 h-11 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-purple-300">
                    <ShieldCheck size={20} />
                  </span>
                  <span>Messages are sent through the server, not exposed in the browser.</span>
                </div>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="glass-panel rounded-2xl p-6 md:p-8">
              <div className="grid md:grid-cols-2 gap-5">
                <label className="block">
                  <span className="form-label-premium">Name</span>
                  <input
                    className="form-input-premium px-4"
                    name="name"
                    value={form.name}
                    onChange={updateField}
                    placeholder="Your name"
                    required
                  />
                </label>
                <label className="block">
                  <span className="form-label-premium">Email</span>
                  <input
                    className="form-input-premium px-4"
                    type="email"
                    name="email"
                    value={form.email}
                    onChange={updateField}
                    placeholder="you@example.com"
                    required
                  />
                </label>
              </div>

              <label className="block mt-5">
                <span className="form-label-premium">Subject</span>
                <input
                  className="form-input-premium px-4"
                  name="subject"
                  value={form.subject}
                  onChange={updateField}
                  placeholder="How can we help?"
                  required
                />
              </label>

              <label className="block mt-5">
                <span className="form-label-premium">Message</span>
                <textarea
                  className="form-input-premium px-4 min-h-40 resize-y"
                  name="message"
                  value={form.message}
                  onChange={updateField}
                  placeholder="Share the details..."
                  required
                />
              </label>

              {status.message && (
                <div
                  className={`mt-5 rounded-xl border px-4 py-3 text-sm ${
                    status.type === 'success'
                      ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200'
                      : 'border-rose-500/30 bg-rose-500/10 text-rose-200'
                  }`}
                >
                  {status.message}
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="auth-btn-primary mt-6 inline-flex items-center justify-center gap-2"
              >
                {submitting ? 'Sending...' : 'Send message'}
                <Send size={16} />
              </button>
            </form>
          </div>
        </section>
      </main>

      <LandingFooter />
    </div>
  );
};

export default ContactPage;
