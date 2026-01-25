import { Link } from 'react-router-dom';
import { Sparkles, FileText, Video, Youtube, ArrowRight } from 'lucide-react';
import { Button, Card, Badge } from '../components/ui';
import { useAuth } from '../context';

export function LandingPage() {
  const { isAuthenticated } = useAuth();

  const modes = [
    {
      icon: Sparkles,
      title: 'AI Tutor',
      description: 'Personalized AI lesson plans',
      available: true,
    },
    {
      icon: FileText,
      title: 'Document Chat',
      description: 'Chat with PDFs and docs',
      available: false,
    },
    {
      icon: Video,
      title: 'Video Learning',
      description: 'Learn from video content',
      available: false,
    },
    {
      icon: Youtube,
      title: 'YouTube Tutor',
      description: 'Chat with YouTube videos',
      available: false,
    },
  ];

  return (
    <div className="min-h-screen bg-dark">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-dark/95 backdrop-blur border-b border-dark-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="text-xl font-bold text-white">
              DocLearn
            </Link>
            
            <nav className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-gray-400 hover:text-white transition-colors">
                Features
              </a>
              <a href="#pricing" className="text-gray-400 hover:text-white transition-colors">
                Pricing
              </a>
            </nav>

            <div className="flex items-center gap-4">
              {isAuthenticated ? (
                <Link to="/dashboard">
                  <Button>Dashboard</Button>
                </Link>
              ) : (
                <>
                  <Link to="/login" className="text-gray-400 hover:text-white transition-colors">
                    Login
                  </Link>
                  <Link to="/register">
                    <Button>Sign Up</Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 md:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
            Learn Anything, Your Way
          </h1>
          <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
            AI-powered personalized learning with multiple modes
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to={isAuthenticated ? '/dashboard' : '/register'}>
              <Button size="lg" rightIcon={<ArrowRight className="w-5 h-5" />}>
                Get Started
              </Button>
            </Link>
            <a href="#features">
              <Button variant="outline" size="lg">
                Learn More
              </Button>
            </a>
          </div>
        </div>
      </section>

      {/* Modes Section */}
      <section id="features" className="py-20 bg-dark-card/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-white text-center mb-12">
            Choose How You Learn
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {modes.map((mode) => (
              <Card
                key={mode.title}
                className={`relative ${!mode.available ? 'opacity-50' : ''}`}
                padding="lg"
              >
                <div className="absolute top-4 right-4">
                  <Badge variant={mode.available ? 'success' : 'gray'}>
                    {mode.available ? 'AVAILABLE' : 'COMING SOON'}
                  </Badge>
                </div>
                
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${
                  mode.available ? 'bg-primary/20' : 'bg-dark-border'
                }`}>
                  <mode.icon className={`w-6 h-6 ${mode.available ? 'text-primary' : 'text-gray-500'}`} />
                </div>
                
                <h3 className="text-lg font-semibold text-white mb-2">{mode.title}</h3>
                <p className="text-gray-400 text-sm">{mode.description}</p>
                
                {mode.available && (
                  <div className="mt-4 pt-4 border-t border-dark-border">
                    <span className="text-xs text-green-500 flex items-center gap-1">
                      <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                      Ready to use
                    </span>
                  </div>
                )}
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Start Learning?
          </h2>
          <p className="text-gray-400 mb-8">
            Create your personalized AI learning plan in seconds
          </p>
          <Link to={isAuthenticated ? '/dashboard' : '/register'}>
            <Button size="lg">
              {isAuthenticated ? 'Go to Dashboard' : 'Create Free Account'}
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-dark-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-gray-500 text-sm">
              © 2026 DocLearn. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              <a href="#" className="text-gray-500 hover:text-gray-400 text-sm">
                Privacy Policy
              </a>
              <a href="#" className="text-gray-500 hover:text-gray-400 text-sm">
                Terms of Service
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
