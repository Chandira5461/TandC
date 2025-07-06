import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { Clock, Share2, Copy, Trophy, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import axios from 'axios';

const TCAuditorGame = () => {
  const [gameState, setGameState] = useState('welcome'); // welcome, reading, quiz, results
  const [currentGame, setCurrentGame] = useState(null);
  const [timeLeft, setTimeLeft] = useState(30);
  const [selectedClauses, setSelectedClauses] = useState([]);
  const [score, setScore] = useState(null);
  const [userAnswers, setUserAnswers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId] = useState(() => Math.random().toString(36).substr(2, 9));
  const [gameStartTime, setGameStartTime] = useState(null);
  const { toast } = useToast();

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

  // Load today's game data
  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    loadGameData(today);
  }, []);

  const loadGameData = async (date) => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API}/game/${date}`);
      setCurrentGame(response.data);
    } catch (err) {
      console.error('Error loading game data:', err);
      setError('Failed to load today\'s game. Please try again.');
      toast({
        title: "Error",
        description: "Failed to load today's game. Please try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  // Timer logic
  useEffect(() => {
    let interval;
    if (gameState === 'reading' && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);
    } else if (timeLeft === 0 && gameState === 'reading') {
      setGameState('quiz');
    }
    return () => clearInterval(interval);
  }, [gameState, timeLeft]);

  const startGame = () => {
    setGameState('reading');
    setTimeLeft(30);
    setSelectedClauses([]);
    setScore(null);
    setUserAnswers([]);
    setGameStartTime(Date.now());
  };

  const submitQuiz = async () => {
    if (selectedClauses.length !== 5) {
      toast({
        title: "Incomplete Selection",
        description: "Please select exactly 5 clauses.",
        variant: "destructive"
      });
      return;
    }

    try {
      setLoading(true);
      
      const completionTime = gameStartTime ? Math.floor((Date.now() - gameStartTime) / 1000) : 0;
      
      const response = await axios.post(`${API}/game/submit`, {
        game_date: currentGame.date,
        session_id: sessionId,
        selected_clauses: selectedClauses,
        completion_time: completionTime
      });

      const scoreData = response.data;
      
      setScore({
        base: scoreData.base_score,
        bonus: scoreData.bonus_score,
        total: scoreData.total_score,
        maxScore: scoreData.max_score,
        breakdown: scoreData.legal_detector_breakdown
      });

      // Create user answers for results display
      const realClauseIds = currentGame.real_absurd_clauses.map(c => c.id);
      const allClauses = [...currentGame.real_absurd_clauses, ...currentGame.fake_absurd_clauses];
      const answers = currentGame.quiz_order.map(clauseId => {
        const clause = allClauses.find(c => c.id === clauseId);
        const isReal = realClauseIds.includes(clauseId);
        const wasSelected = selectedClauses.includes(clauseId);
        return {
          id: clauseId,
          text: clause.text,
          isReal,
          wasSelected,
          correct: (isReal && wasSelected) || (!isReal && !wasSelected)
        };
      });
      
      setUserAnswers(answers);
      setGameState('results');
      
    } catch (err) {
      console.error('Error submitting quiz:', err);
      toast({
        title: "Submission Error",
        description: "Failed to submit your results. Please try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const generateShareText = () => {
    const realClauseIds = currentGame.real_absurd_clauses.map(c => c.id);
    const emoji = currentGame.quiz_order.map(clauseId => {
      const isReal = realClauseIds.includes(clauseId);
      const wasSelected = selectedClauses.includes(clauseId);
      
      if (isReal && wasSelected) return '✅'; // Correct identification
      if (isReal && !wasSelected) return '❌'; // Missed real clause
      if (!isReal && wasSelected) return '❌'; // Selected fake clause
      return '⚪'; // Correctly ignored fake clause
    }).join('');

    return `T&C Auditor ${new Date().toLocaleDateString()}
Legal Detector Score: ${score.total.toFixed(1)}/5.0

${emoji}

Can you spot the absurd clauses? Play at tc-auditor.com`;
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(generateShareText());
      toast({
        title: "Copied to clipboard!",
        description: "Share your results with friends.",
      });
    } catch (err) {
      toast({
        title: "Copy failed",
        description: "Please try again.",
        variant: "destructive"
      });
    }
  };

  const shareToTwitter = () => {
    const text = encodeURIComponent(generateShareText());
    window.open(`https://twitter.com/intent/tweet?text=${text}`, '_blank');
  };

  if (!currentGame) {
    return <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="text-center">Loading today's audit...</div>
    </div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Welcome State */}
      {gameState === 'welcome' && (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
          <div className="text-center mb-8">
            <h1 className="text-6xl font-bold text-gray-900 mb-4">
              T&C Auditor
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              The daily game that tests your ability to spot absurd clauses in Terms & Conditions
            </p>
            <div className="bg-white rounded-lg p-6 shadow-lg mb-8">
              <h2 className="text-2xl font-semibold mb-4">How to Play</h2>
              <div className="grid md:grid-cols-3 gap-4 text-left">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-5 h-5 text-blue-600" />
                    <span className="font-medium">1. Speed Read</span>
                  </div>
                  <p className="text-sm text-gray-600">Scan the T&C document for 30 seconds</p>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="font-medium">2. Identify</span>
                  </div>
                  <p className="text-sm text-gray-600">Select 5 clauses that were actually in the document</p>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Trophy className="w-5 h-5 text-yellow-600" />
                    <span className="font-medium">3. Score</span>
                  </div>
                  <p className="text-sm text-gray-600">Get your Legal Detector score and share!</p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="text-center">
            <Button 
              onClick={startGame}
              size="lg"
              className="text-xl px-8 py-6 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 transform hover:scale-105 transition-all duration-200"
            >
              Play Today's Audit
            </Button>
          </div>
        </div>
      )}

      {/* Reading State */}
      {gameState === 'reading' && (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
          <div className="mb-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">Speed Reading Phase</h2>
              <div className="flex items-center space-x-4">
                <Clock className="w-6 h-6 text-red-500" />
                <span className="text-3xl font-bold text-red-500">{timeLeft}s</span>
              </div>
            </div>
            <Progress value={(30 - timeLeft) / 30 * 100} className="h-2" />
            <p className="text-sm text-gray-600 mt-2">
              Quickly scan this document for absurd, unusual, or suspicious clauses. You'll be tested on them!
            </p>
          </div>

          <Card className="h-96 overflow-y-auto">
            <CardHeader>
              <CardTitle className="text-lg">{currentGame.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="whitespace-pre-line text-sm leading-relaxed">
                {currentGame.tc_text}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Quiz State */}
      {gameState === 'quiz' && (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-4">Clause Identification</h2>
            <p className="text-gray-600 mb-4">
              Select exactly 5 clauses that were actually present in the document you just read.
            </p>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-500">
                Selected: {selectedClauses.length}/5
              </span>
              <Button 
                onClick={submitQuiz}
                disabled={selectedClauses.length !== 5}
                className="bg-green-600 hover:bg-green-700"
              >
                Submit Audit
              </Button>
            </div>
          </div>

          <div className="space-y-4">
            {currentGame.quiz_order.map((clauseId, index) => {
              const allClauses = [...currentGame.real_absurd_clauses, ...currentGame.fake_absurd_clauses];
              const clause = allClauses.find(c => c.id === clauseId);
              const isSelected = selectedClauses.includes(clauseId);
              
              return (
                <Card 
                  key={clauseId}
                  className={`cursor-pointer transition-all duration-200 ${
                    isSelected 
                      ? 'ring-2 ring-blue-500 bg-blue-50' 
                      : 'hover:shadow-md'
                  }`}
                  onClick={() => {
                    if (isSelected) {
                      setSelectedClauses(prev => prev.filter(id => id !== clauseId));
                    } else if (selectedClauses.length < 5) {
                      setSelectedClauses(prev => [...prev, clauseId]);
                    }
                  }}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start space-x-3">
                      <Badge variant="outline" className="mt-1">
                        {String.fromCharCode(65 + index)}
                      </Badge>
                      <p className="text-sm flex-1">{clause.text}</p>
                      {isSelected && (
                        <CheckCircle className="w-5 h-5 text-blue-600 mt-1" />
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Results State */}
      {gameState === 'results' && (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-4">Audit Complete!</h2>
            <div className="bg-white rounded-lg p-6 shadow-lg mb-6">
              <div className="text-6xl font-bold text-blue-600 mb-2">
                {score.total.toFixed(1)}
              </div>
              <div className="text-xl text-gray-600 mb-4">Legal Detector Score</div>
              <div className="text-sm text-gray-500">
                Base Score: {score.base}/5 + Bonus: {score.bonus.toFixed(1)}
              </div>
            </div>
            
            <div className="flex justify-center space-x-4 mb-8">
              <Button onClick={copyToClipboard} variant="outline" size="sm">
                <Copy className="w-4 h-4 mr-2" />
                Copy Results
              </Button>
              <Button onClick={shareToTwitter} variant="outline" size="sm">
                <Share2 className="w-4 h-4 mr-2" />
                Share on X
              </Button>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-xl font-semibold mb-4">Today's Real Absurd Clauses</h3>
            {currentGame.real_absurd_clauses.map(clause => (
              <Card key={clause.id} className="bg-green-50 border-green-200">
                <CardContent className="p-4">
                  <div className="flex items-start space-x-3">
                    <CheckCircle className="w-5 h-5 text-green-600 mt-1" />
                    <p className="text-sm">{clause.text}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="text-center mt-8">
            <Button 
              onClick={() => setGameState('welcome')}
              variant="outline"
            >
              Play Again Tomorrow
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TCAuditorGame;