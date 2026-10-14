import React from "react";
import {
  Compass,
  Sparkles,
  ArrowRight,
  Plane,
  Package,
  ShieldCheck,
  Zap,
  Globe,
  Truck,
  MessageSquare,
  Bot,
  ExternalLink,
  ChevronRight,
  CheckCircle2,
  Lock
} from "lucide-react";

export default function PublicLandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-sky-500 selection:text-white relative overflow-hidden">
      {/* Background ambient gradient glows */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-gradient-to-tr from-sky-600/15 via-blue-600/10 to-indigo-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-0 w-[600px] h-[400px] bg-gradient-to-bl from-indigo-600/10 via-violet-600/10 to-transparent rounded-full blur-3xl pointer-events-none" />

      {/* Header / Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-900/70 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-blue-600 flex items-center justify-center shadow-lg shadow-sky-500/25">
              <Compass className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-white block leading-tight">Travelogix</span>
              <span className="text-[10px] text-sky-400 font-medium tracking-wider uppercase block">Unified Platform</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-8 text-sm font-medium text-slate-300">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#architecture" className="hover:text-white transition-colors">How It Works</a>
            <a href="#capabilities" className="hover:text-white transition-colors">Capabilities</a>
            <a href="#faq" className="hover:text-white transition-colors">FAQ</a>
          </nav>

          {/* CTA Actions */}
          <div className="flex items-center space-x-3">
            <a
              href="http://localhost:3000/login"
              className="text-xs sm:text-sm font-medium text-slate-300 hover:text-white px-3.5 py-2 rounded-xl hover:bg-slate-800/80 transition-colors"
            >
              Customer Login
            </a>
            <a
              href="http://localhost:3000/register"
              className="hidden sm:inline-flex text-xs sm:text-sm font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 px-4 py-2 rounded-xl transition-all"
            >
              Create Account
            </a>
            <a
              href="http://localhost:3000/ai-assistant"
              className="text-xs sm:text-sm font-semibold bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white px-4 py-2 rounded-xl shadow-lg shadow-sky-500/20 transition-all flex items-center space-x-1.5"
            >
              <Sparkles className="w-4 h-4" />
              <span>Start AI Assistant</span>
            </a>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-20 text-center relative z-10">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-semibold uppercase tracking-wider mb-8 backdrop-blur-sm">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Next-Generation Multi-Agent AI</span>
          </div>

          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white mb-6 max-w-4xl mx-auto leading-tight sm:leading-tight">
            Travel &amp; Logistics in <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-blue-400 to-indigo-400">One AI Chat</span>
          </h1>

          <p className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto mb-10 leading-relaxed font-normal">
            Travelogix unifies multi-modal travel planning, flight &amp; train telemetry, and end-to-end freight logistics into one intelligent conversational assistant.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <a
              href="http://localhost:3000/ai-assistant"
              className="w-full sm:w-auto inline-flex items-center justify-center space-x-3 px-8 py-4 rounded-2xl bg-gradient-to-r from-sky-500 via-blue-600 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-bold text-base shadow-xl shadow-sky-500/25 hover:shadow-sky-500/40 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <Bot className="w-5 h-5" />
              <span>Start AI Assistant</span>
              <ArrowRight className="w-5 h-5" />
            </a>
            <a
              href="http://localhost:3000/login"
              className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-7 py-4 rounded-2xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 font-semibold text-base transition-all"
            >
              <span>Customer Sign In</span>
            </a>
            <a
              href="http://localhost:3001/admin/login"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-4 rounded-2xl bg-slate-900/60 hover:bg-slate-800/80 text-slate-400 hover:text-slate-200 border border-slate-800 text-sm font-medium transition-all"
            >
              <Lock className="w-4 h-4 text-indigo-400" />
              <span>Admin Portal</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>

          {/* Interactive Preview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto text-left">
            <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-md hover:border-sky-500/40 transition-colors">
              <div className="w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center mb-4">
                <Plane className="w-6 h-6 text-sky-400" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Smart Travel AI</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Instant flight &amp; train schedules, multi-city trip itineraries, budget estimation, hotel search, and live weather reports.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-md hover:border-blue-500/40 transition-colors">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-4">
                <Package className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Autonomous Logistics</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Register cargo parcels, obtain instant tracking tokens, monitor real-time location updates, driver assignment, and delivery ETAs.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-md hover:border-indigo-500/40 transition-colors">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-4">
                <ShieldCheck className="w-6 h-6 text-indigo-400" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Operations Portal</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Dedicated administrative console for fleet managers to control drivers, dispatch vehicles, resolve delayed cargo, and analyze telemetry.
              </p>
            </div>
          </div>
        </section>

        {/* Features & Architecture Grid */}
        <section id="features" className="py-16 bg-slate-900/40 border-y border-slate-800/80">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-2xl mx-auto mb-14">
              <h2 className="text-2xl sm:text-4xl font-extrabold text-white mb-4">
                One Conversational Interface for Everything
              </h2>
              <p className="text-sm sm:text-base text-slate-400">
                Powered by FastAPI, PostgreSQL, Redis session caching, and intent-driven agent tools.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                {
                  title: "Multi-Intent AI Engine",
                  desc: "Automatically route queries to specialized travel, transport, and freight agents.",
                  icon: Zap,
                  color: "text-amber-400",
                },
                {
                  title: "Real-Time Telemetry",
                  desc: "Live GPS updates, ETA estimation, and driver status tracking.",
                  icon: Truck,
                  color: "text-emerald-400",
                },
                {
                  title: "FastAPI Backend",
                  desc: "High-performance Python backend with PostgreSQL source-of-truth persistence.",
                  icon: Globe,
                  color: "text-sky-400",
                },
                {
                  title: "Role-Based Security",
                  desc: "Strict session separation between Customer Chatbot and Admin Operations.",
                  icon: Lock,
                  color: "text-indigo-400",
                },
              ].map((feat, idx) => {
                const Icon = feat.icon;
                return (
                  <div key={idx} className="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
                    <Icon className={`w-7 h-7 ${feat.color}`} />
                    <h3 className="text-base font-bold text-white">{feat.title}</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">{feat.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section id="faq" className="py-16 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white text-center mb-10">
            Frequently Asked Questions
          </h2>

          <div className="space-y-4">
            {[
              {
                q: "What is Travelogix?",
                a: "Travelogix is a unified platform combining consumer travel assistance (flights, hotels, trains, itineraries) with logistics management (parcel booking, shipment tracking) into one AI assistant.",
              },
              {
                q: "How do I access the AI Assistant?",
                a: "Click on 'Start AI Assistant' or visit http://localhost:3000/ai-assistant to chat with Travelogix AI.",
              },
              {
                q: "How do logistics managers log in?",
                a: "Logistics admins can access the Operations Console at http://localhost:3001/admin/login using authorized admin credentials.",
              },
            ].map((faq, i) => (
              <div key={i} className="p-5 rounded-2xl bg-slate-900 border border-slate-800">
                <h3 className="text-base font-bold text-white mb-2 flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-sky-400 shrink-0" />
                  <span>{faq.q}</span>
                </h3>
                <p className="text-sm text-slate-400 pl-6 leading-relaxed">{faq.a}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Bottom CTA */}
        <section className="py-16 bg-gradient-to-b from-transparent to-slate-900/60 text-center border-t border-slate-800/80">
          <div className="max-w-3xl mx-auto px-4">
            <h2 className="text-3xl font-extrabold text-white mb-4">Ready to Experience Travelogix?</h2>
            <p className="text-slate-400 text-sm mb-8">Start chatting with our multi-agent AI assistant right away.</p>
            <a
              href="http://localhost:3000/ai-assistant"
              className="inline-flex items-center space-x-2 px-8 py-4 rounded-2xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-bold text-base shadow-xl shadow-sky-500/25 transition-all hover:scale-105"
            >
              <span>Launch AI Assistant</span>
              <ArrowRight className="w-5 h-5" />
            </a>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/60 py-6 text-xs text-slate-500 relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <Compass className="w-4 h-4 text-sky-400" />
            <span className="font-semibold text-slate-300">Travelogix</span>
            <span>&bull; Travel &amp; Logistics in One Chat</span>
          </div>

          <div className="flex items-center space-x-6 text-slate-400">
            <a href="http://localhost:3000/login" className="hover:text-white transition-colors">Customer Login</a>
            <a href="http://localhost:3000/register" className="hover:text-white transition-colors">Register</a>
            <a
              href="http://localhost:3001/admin/login"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sky-400 hover:text-sky-300 font-medium inline-flex items-center space-x-1"
            >
              <span>Admin Portal</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
