import { Link } from 'react-router-dom';
import { Check, ArrowRight, Home } from 'lucide-react';
import { Button, Card } from '../components/ui';

interface CourseCompletePageProps {
  topic?: string;
  days?: number;
  hours?: number;
  topics?: number;
}

export function CourseCompletePage({ 
  topic = 'Your Course',
  days = 7,
  hours = 7,
  topics = 15,
}: CourseCompletePageProps) {
  return (
    <div className="max-w-lg mx-auto text-center py-12">
      {/* Success Icon */}
      <div className="w-20 h-20 mx-auto mb-6 bg-primary rounded-full flex items-center justify-center">
        <Check className="w-10 h-10 text-white" />
      </div>

      <h1 className="text-3xl font-bold text-white mb-2">Congratulations!</h1>
      <p className="text-gray-400 mb-1">You've completed</p>
      <p className="text-xl font-semibold text-white mb-8">{topic}</p>

      {/* Stats */}
      <Card className="mb-8">
        <div className="grid grid-cols-3 divide-x divide-dark-border">
          <div className="px-4 py-6 text-center">
            <p className="text-3xl font-bold text-white">{days}</p>
            <p className="text-sm text-gray-400">Days</p>
          </div>
          <div className="px-4 py-6 text-center">
            <p className="text-3xl font-bold text-white">{hours}</p>
            <p className="text-sm text-gray-400">Hours</p>
          </div>
          <div className="px-4 py-6 text-center">
            <p className="text-3xl font-bold text-white">{topics}</p>
            <p className="text-sm text-gray-400">Topics</p>
          </div>
        </div>
      </Card>

      {/* Actions */}
      <div className="space-y-3">
        <Link to="/sessions/new" className="block">
          <Button className="w-full">
            Start New Session
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </Link>
        <Link to="/dashboard" className="block">
          <Button variant="outline" className="w-full">
            <Home className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
        </Link>
      </div>

      <Link to="/sessions" className="inline-block mt-6 text-sm text-gray-400 hover:text-white underline">
        View session details
      </Link>
    </div>
  );
}
