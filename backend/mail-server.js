const cors = require('cors');
const dotenv = require('dotenv');
const express = require('express');
const nodemailer = require('nodemailer');

dotenv.config();

const app = express();
const port = Number(process.env.MAIL_SERVER_PORT || 4000);
const mailUser = process.env.GMAIL_USER;
const mailPass = process.env.GMAIL_APP_PASSWORD;
const toAddress = process.env.CONTACT_TO_EMAIL || mailUser;

app.use(cors({ origin: process.env.FRONTEND_ORIGIN || 'http://localhost:5173' }));
app.use(express.json({ limit: '20kb' }));

const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: mailUser,
    pass: mailPass,
  },
});

const required = ['name', 'email', 'subject', 'message'];

app.get('/contact-api/health', (_request, response) => {
  response.json({
    ok: true,
    gmailConfigured: Boolean(mailUser && mailPass),
    resetMode: 'code',
  });
});

app.post('/contact-api/send', async (request, response) => {
  if (!mailUser || !mailPass) {
    return response.status(500).json({ error: 'Mail server is missing Gmail credentials.' });
  }

  const payload = request.body || {};
  const missing = required.filter((field) => !String(payload[field] || '').trim());

  if (missing.length > 0) {
    return response.status(400).json({ error: `Missing required fields: ${missing.join(', ')}` });
  }

  const name = String(payload.name).trim().slice(0, 120);
  const email = String(payload.email).trim().slice(0, 160);
  const subject = String(payload.subject).trim().slice(0, 180);
  const message = String(payload.message).trim().slice(0, 5000);

  try {
    await transporter.sendMail({
      from: `"SkillTree Contact" <${mailUser}>`,
      to: toAddress,
      replyTo: email,
      subject: `SkillTree.AI Contact: ${subject}`,
      text: [
        `Name: ${name}`,
        `Email: ${email}`,
        `Subject: ${subject}`,
        '',
        message,
      ].join('\n'),
      html: `
        <h2>New SkillTree.AI contact message</h2>
        <p><strong>Name:</strong> ${escapeHtml(name)}</p>
        <p><strong>Email:</strong> ${escapeHtml(email)}</p>
        <p><strong>Subject:</strong> ${escapeHtml(subject)}</p>
        <p style="white-space: pre-line;">${escapeHtml(message)}</p>
      `,
    });

    response.json({ ok: true });
  } catch (error) {
    console.error('Failed to send contact email:', error);
    response.status(502).json({ error: 'Failed to send message. Check Gmail app password and SMTP access.' });
  }
});

app.post('/auth-mail/welcome', async (request, response) => {
  if (!mailUser || !mailPass) {
    return response.status(500).json({ error: 'Mail server is missing Gmail credentials.' });
  }

  const email = String(request.body?.email || '').trim();
  const username = String(request.body?.username || 'Builder').trim();

  if (!email) {
    return response.status(400).json({ error: 'Email is required.' });
  }

  try {
    await transporter.sendMail({
      from: `"SkillTree.AI" <${mailUser}>`,
      to: email,
      subject: 'Welcome to SkillTree.AI',
      text: `Thank you for registering on SkillTree.AI, ${username}. Your learning journey is ready.`,
      html: welcomeEmailTemplate(username),
    });

    response.json({ ok: true });
  } catch (error) {
    console.error('Failed to send welcome email:', error);
    response.status(502).json({ error: 'Failed to send welcome email.' });
  }
});

app.post('/auth-mail/password-reset', async (request, response) => {
  if (!mailUser || !mailPass) {
    return response.status(500).json({ error: 'Mail server is missing Gmail credentials.' });
  }

  const email = String(request.body?.email || '').trim();
  const username = String(request.body?.username || 'Builder').trim();
  const resetCode = String(request.body?.resetCode || '').trim().toUpperCase();
  const expiresInMinutes = Number(request.body?.expiresInMinutes || 4);

  if (!email || !resetCode) {
    return response.status(400).json({ error: 'Email and resetCode are required.' });
  }

  try {
    await transporter.sendMail({
      from: `"SkillTree.AI Security" <${mailUser}>`,
      to: email,
      subject: 'Reset your SkillTree.AI password',
      text: `Use this code to reset your password: ${resetCode}. It expires in ${expiresInMinutes} minutes.`,
      html: passwordResetTemplate(username, resetCode, expiresInMinutes),
    });

    response.json({ ok: true });
  } catch (error) {
    console.error('Failed to send password reset email:', error);
    response.status(502).json({ error: 'Failed to send password reset email.' });
  }
});

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function welcomeEmailTemplate(username) {
  const safeUsername = escapeHtml(username);

  return baseEmailTemplate(`
    <p style="margin:0 0 10px;color:#a5b4fc;font-size:12px;font-weight:700;letter-spacing:1.8px;text-transform:uppercase;">Registration Complete</p>
    <h1 style="margin:0;color:#ffffff;font-size:34px;line-height:1.05;letter-spacing:-1px;">Welcome to SkillTree.AI, ${safeUsername}.</h1>
    <p style="margin:22px 0 0;color:#cbd5e1;font-size:16px;line-height:1.7;">
      Thank you for registering on our website. Your account is ready, and your adaptive learning journey can begin now.
    </p>
    <div style="margin:28px 0;padding:18px;border:1px solid rgba(148,163,184,0.22);border-radius:14px;background:rgba(15,23,42,0.7);">
      <p style="margin:0;color:#f8fafc;font-size:15px;font-weight:700;">What you can do next</p>
      <ul style="margin:14px 0 0;padding-left:20px;color:#cbd5e1;line-height:1.8;font-size:14px;">
        <li>Build a personalized skill tree.</li>
        <li>Start quests and track XP progress.</li>
        <li>Use the AI mentor when you get stuck.</li>
      </ul>
    </div>
    <a href="${escapeHtml(process.env.FRONTEND_URL || 'http://localhost:5173')}/dashboard" style="display:inline-block;background:linear-gradient(135deg,#6366f1,#f43f5e);color:#ffffff;text-decoration:none;font-weight:800;font-size:13px;letter-spacing:1px;text-transform:uppercase;padding:14px 20px;border-radius:10px;">Open Dashboard</a>
  `);
}

function passwordResetTemplate(username, resetCode, expiresInMinutes) {
  const safeUsername = escapeHtml(username);
  const safeResetCode = escapeHtml(resetCode);

  return baseEmailTemplate(`
    <p style="margin:0 0 10px;color:#fda4af;font-size:12px;font-weight:700;letter-spacing:1.8px;text-transform:uppercase;">Password Reset</p>
    <h1 style="margin:0;color:#ffffff;font-size:32px;line-height:1.08;letter-spacing:-1px;">Reset your security key, ${safeUsername}.</h1>
    <p style="margin:22px 0 0;color:#cbd5e1;font-size:16px;line-height:1.7;">
      We received a request to reset your SkillTree.AI password. This code expires in ${expiresInMinutes} minutes.
    </p>
    <div style="display:inline-block;margin:28px 0 18px;background:rgba(15,23,42,0.85);border:1px solid rgba(196,181,253,0.35);border-radius:14px;padding:16px 22px;color:#ffffff;font-size:30px;font-weight:900;letter-spacing:8px;">${safeResetCode}</div>
    <p style="margin:24px 0 0;color:#64748b;font-size:13px;line-height:1.6;">
      If you did not request this, you can ignore this email. Your current password will stay unchanged.
    </p>
  `);
}

function baseEmailTemplate(content) {
  return `
    <!doctype html>
    <html>
      <body style="margin:0;background:#020617;font-family:Arial,Helvetica,sans-serif;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#020617;padding:32px 14px;">
          <tr>
            <td align="center">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:620px;border:1px solid rgba(148,163,184,0.22);border-radius:22px;overflow:hidden;background:linear-gradient(145deg,#0f172a,#050816);">
                <tr>
                  <td style="padding:34px 32px 28px;">
                    <div style="display:inline-block;margin-bottom:24px;padding:10px 13px;border-radius:14px;background:linear-gradient(135deg,#6366f1,#f43f5e);color:#ffffff;font-weight:900;letter-spacing:-0.5px;">SkillTree.AI</div>
                    ${content}
                  </td>
                </tr>
                <tr>
                  <td style="padding:18px 32px;border-top:1px solid rgba(148,163,184,0.16);color:#64748b;font-size:12px;line-height:1.6;">
                    SkillTree.AI · Adaptive learning for builders
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
  `;
}

app.listen(port, () => {
  console.log(`Mail server listening on http://127.0.0.1:${port}`);
});
