/**
 * ContactSection Component
 * Terminal-flavored contact panel as the final node in the page's circuit.
 */

import { useState } from 'react';
import { ArrowUpRight, Mail, ShieldCheck } from 'lucide-react';
import useScrollAnimation from '../../hooks/useScrollAnimation';

const initialForm = { name: '', email: '', subject: '', message: '' };

const ContactSection = () => {
  const { ref, className } = useScrollAnimation({ threshold: 0.2 });
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
      setStatus({ type: 'success', message: 'Message sent. We\'ll get back to you soon.' });
    } catch (error) {
      setStatus({ type: 'error', message: error.message });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section
      id="contact"
      ref={ref}
      className={`relative py-24 px-6 bg-[#050505] ${className} animate-in-default`}
    >
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-14">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm mb-4">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              ✦ LAST NODE
            </span>
          </div>
          <h2 className="text-5xl font-black tracking-tighter mb-4 text-white">
            Open a line.
          </h2>
          <p className="text-lg text-slate-400 max-w-xl mx-auto">
            Questions, feedback, or bug reports — all land in the same inbox, and a real person replies.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="relative bg-white/[0.03] border border-white/10 rounded-2xl overflow-hidden"
        >
          {/* Terminal Titlebar */}
          <div className="flex items-center gap-2 px-5 py-3 border-b border-white/10 bg-black/40">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
            <div className="w-2.5 h-2.5 rounded-full bg-white/20" />
            <div className="w-2.5 h-2.5 rounded-full bg-white/20" />
            <span className="ml-2 text-xs font-mono text-slate-500">send_message.sh</span>
          </div>

          <div className="p-6 md:p-8">
            <div className="grid md:grid-cols-2 gap-5">
              <label className="block">
                <span className="block text-xs font-mono text-red-400/80 uppercase tracking-wider mb-2">// name</span>
                <input
                  className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/20 transition-all"
                  name="name"
                  value={form.name}
                  onChange={updateField}
                  placeholder="Your name"
                  required
                />
              </label>
              <label className="block">
                <span className="block text-xs font-mono text-red-400/80 uppercase tracking-wider mb-2">// email</span>
                <input
                  className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/20 transition-all"
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
              <span className="block text-xs font-mono text-red-400/80 uppercase tracking-wider mb-2">// subject</span>
              <input
                className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/20 transition-all"
                name="subject"
                value={form.subject}
                onChange={updateField}
                placeholder="How can we help?"
                required
              />
            </label>

            <label className="block mt-5">
              <span className="block text-xs font-mono text-red-400/80 uppercase tracking-wider mb-2">// message</span>
              <textarea
                className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/20 transition-all min-h-32 resize-y font-mono text-sm"
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

            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 mt-8">
              <div className="flex flex-col gap-2 text-sm text-slate-500">
                <div className="flex items-center gap-2">
                  <Mail size={14} className="text-red-400" />
                  <span>ishitrathod6@gmail.com</span>
                </div>
                <div className="flex items-center gap-2">
                  <ShieldCheck size={14} className="text-red-400" />
                  <span>Sent through the server — never exposed client-side.</span>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="magnetic-btn px-8 py-3 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-semibold rounded-lg transition-colors inline-flex items-center justify-center gap-2 whitespace-nowrap"
              >
                {submitting ? 'Sending...' : 'Send message'}
                <ArrowUpRight size={16} />
              </button>
            </div>
          </div>
        </form>
      </div>
    </section>
  );
};

export default ContactSection;
