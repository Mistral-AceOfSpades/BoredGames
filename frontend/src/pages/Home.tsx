import { Link } from 'react-router-dom';
import { Search, Upload, Gamepad2, MessageCircle, Scale, Sparkles } from 'lucide-react';

const features = [
  {
    icon: Search,
    title: 'Find Any Game',
    description: 'Search for board games by name or upload rulebook images. AI retrieves and structures rules instantly.',
  },
  {
    icon: MessageCircle,
    title: 'Interactive Explanations',
    description: 'Quick start, step-by-step, or simulated playthrough modes. Ask questions with voice or text.',
  },
  {
    icon: Sparkles,
    title: 'House Rule Engine',
    description: 'Add custom rules with AI validation. Detect contradictions, balance impacts, and logical issues.',
  },
  {
    icon: Gamepad2,
    title: 'Live Moderation',
    description: 'AI moderator tracks turns, validates moves, and manages game flow in real time.',
  },
  {
    icon: Scale,
    title: 'Dispute Resolution',
    description: 'Neutral AI arbiter resolves rule disputes with official citations and interpretation hierarchy.',
  },
  {
    icon: Upload,
    title: 'OCR Rulebook Parsing',
    description: 'Upload photos of rulebook pages. Mistral OCR extracts and structures rules automatically.',
  },
];

export function HomePage() {
  return (
    <div className="space-y-16">
      {/* Hero */}
      <section className="text-center py-16">
        <h1 className="font-display text-5xl sm:text-6xl font-bold text-white mb-6">
          Board Games,
          <br />
          <span className="text-brand-400">Without the Boredom</span>
        </h1>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-8">
          AI-powered board game moderator that learns rules, explains gameplay,
          adapts to house rules, and moderates sessions in real time.
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <Link to="/search" className="btn-primary text-lg px-8 py-3">
            Find a Game
          </Link>
          <Link to="/upload" className="btn-secondary text-lg px-8 py-3">
            Upload Rulebook
          </Link>
        </div>
      </section>

      {/* Features */}
      <section>
        <h2 className="font-display text-3xl font-bold text-white text-center mb-12">
          Everything You Need to Play
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <div key={feature.title} className="card hover:border-brand-500/30 transition-colors">
              <feature.icon className="h-10 w-10 text-brand-400 mb-4" />
              <h3 className="font-display text-lg font-semibold text-white mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-gray-400">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="text-center">
        <h2 className="font-display text-3xl font-bold text-white mb-12">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {[
            { step: '1', title: 'Find Your Game', desc: 'Search by name or upload rulebook photos' },
            { step: '2', title: 'Learn the Rules', desc: 'Choose quick start, detailed, or simulated explanation' },
            { step: '3', title: 'Customize', desc: 'Add house rules with AI contradiction checking' },
            { step: '4', title: 'Play!', desc: 'AI moderates turns, resolves disputes, tracks state' },
          ].map((item) => (
            <div key={item.step} className="flex flex-col items-center">
              <div className="w-12 h-12 rounded-full bg-brand-600 flex items-center justify-center text-white font-bold text-lg mb-4">
                {item.step}
              </div>
              <h3 className="font-display font-semibold text-white mb-1">{item.title}</h3>
              <p className="text-sm text-gray-400">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="card text-center py-12 bg-gradient-to-r from-brand-900/50 to-purple-900/50 border-brand-700/30">
        <h2 className="font-display text-2xl font-bold text-white mb-4">
          Ready to transform your game nights?
        </h2>
        <p className="text-gray-400 mb-6">
          Powered by Mistral AI — fast, accurate, and always fair.
        </p>
        <Link to="/search" className="btn-primary">
          Get Started
        </Link>
      </section>
    </div>
  );
}
