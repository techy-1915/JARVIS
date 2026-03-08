import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const features = [
  {
    icon: '🧠',
    title: 'Multi-Model AI Routing',
    desc: 'Automatically routes your queries to the best AI provider — Gemini, Groq, or local models — with seamless fallback.',
  },
  {
    icon: '💬',
    title: 'Intelligent Chat Interface',
    desc: 'ChatGPT-style interface with markdown rendering, syntax-highlighted code blocks, and conversation history.',
  },
  {
    icon: '⚡',
    title: 'Real-Time Streaming',
    desc: 'WebSocket-powered live responses with typing indicators and event logging.',
  },
  {
    icon: '🔒',
    title: 'Secure by Design',
    desc: 'JWT authentication, input validation, sandboxed execution, and bcrypt password hashing.',
  },
  {
    icon: '🔄',
    title: 'Automatic Fallback',
    desc: 'If a cloud provider hits its limit, JARVIS transparently switches to the next best option and notifies you.',
  },
  {
    icon: '📚',
    title: 'Self-Learning',
    desc: 'Continuously improves through conversation logging, feedback collection, and automated dataset generation.',
  },
];

export default function Landing() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
      return;
    }
    // Trigger entrance animation
    const t = setTimeout(() => setVisible(true), 50);
    return () => clearTimeout(t);
  }, [isAuthenticated, navigate]);

  return (
    <div className="min-h-screen bg-[#0d1117] text-white">
      {/* Navigation */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-[#21262d]">
        <div className="flex items-center gap-2">
          <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            JARVIS
          </span>
          <span className="text-xs text-gray-500 mt-1">AI Assistant</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/login')}
            className="px-4 py-2 text-sm text-gray-300 hover:text-white transition-colors"
          >
            Sign In
          </button>
          <button
            onClick={() => navigate('/signup')}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
          >
            Get Started
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section
        className={`flex flex-col items-center text-center px-6 pt-24 pb-20 transition-all duration-700 ${
          visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-xs font-medium mb-6">
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
          Priority-based AI routing with automatic fallback
        </div>

        <h1 className="text-5xl md:text-7xl font-bold leading-tight mb-6">
          Meet{' '}
          <span className="bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 bg-clip-text text-transparent">
            JARVIS
          </span>
        </h1>

        <p className="max-w-2xl text-lg text-gray-400 mb-10">
          Your intelligent AI assistant that routes queries to the best available model,
          handles fallbacks automatically, and keeps getting smarter over time.
        </p>

        <div className="flex flex-col sm:flex-row gap-4">
          <button
            onClick={() => navigate('/signup')}
            className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-xl font-semibold text-lg transition-all duration-200 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40"
          >
            Get Started Free
          </button>
          <button
            onClick={() => navigate('/login')}
            className="px-8 py-3 bg-[#161b22] hover:bg-[#21262d] border border-[#30363d] rounded-xl font-semibold text-lg transition-colors"
          >
            Sign In
          </button>
        </div>
      </section>

      {/* Features */}
      <section className="px-6 pb-24 max-w-6xl mx-auto">
        <h2 className="text-center text-3xl font-bold mb-12 text-gray-100">
          Everything you need in one AI assistant
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f) => (
            <div
              key={f.title}
              className="p-6 bg-[#161b22] border border-[#21262d] rounded-xl hover:border-blue-500/50 transition-colors group"
            >
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="font-semibold text-white mb-2 group-hover:text-blue-400 transition-colors">
                {f.title}
              </h3>
              <p className="text-sm text-gray-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 pb-24 text-center">
        <div className="max-w-2xl mx-auto p-10 bg-gradient-to-br from-blue-600/10 to-purple-600/10 border border-blue-500/20 rounded-2xl">
          <h2 className="text-3xl font-bold mb-4">Ready to get started?</h2>
          <p className="text-gray-400 mb-8">
            Create a free account and start chatting with the smartest AI routing system available.
          </p>
          <button
            onClick={() => navigate('/signup')}
            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 rounded-xl font-semibold transition-colors"
          >
            Create your account
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#21262d] py-6 text-center text-sm text-gray-600">
        JARVIS AI Assistant · MIT License
      </footer>
    </div>
  );
}
