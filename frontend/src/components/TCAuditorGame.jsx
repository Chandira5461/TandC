import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { Clock, Share2, Copy, Trophy, CheckCircle, XCircle, Loader2, Timer, Zap, Target, Volume2, VolumeX } from 'lucide-react';
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
  const [countdown, setCountdown] = useState('');
  const [isAudioEnabled, setIsAudioEnabled] = useState(false);
  const [hasPlayedToday, setHasPlayedToday] = useState(false);
  const { toast } = useToast();

  const audioRef = useRef(null);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

  // Check if user has already played today
  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    const savedResult = localStorage.getItem(`tc_auditor_${today}`);
    if (savedResult) {
      const result = JSON.parse(savedResult);
      setScore(result.score);
      setUserAnswers(result.userAnswers);
      setHasPlayedToday(true);
      loadGameData(today);
    } else {
      loadGameData(today);
    }
  }, []);

  // Countdown to tomorrow's challenge
  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date();
      const tomorrow = new Date(now);
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(0, 0, 0, 0);
      
      const timeDiff = tomorrow - now;
      const hours = Math.floor(timeDiff / (1000 * 60 * 60));
      const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);
      
      setCountdown(`${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
    return () => clearInterval(interval);
  }, []);

  const loadGameData = async (date) => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API}/game/${date}`);
      setCurrentGame(response.data);
      
      // If user has already played today, show their results
      if (hasPlayedToday) {
        setGameState('results');
      }
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
        setTimeLeft(prev => {
          const newTime = prev - 1;
          
          // Haptic feedback for last 10 seconds
          if (newTime <= 10 && newTime > 0) {
            // Vibrate on mobile devices
            if (navigator.vibrate) {
              navigator.vibrate(50); // 50ms vibration
            }
          }
          
          return newTime;
        });
      }, 1000);
    } else if (timeLeft === 0 && gameState === 'reading') {
      // Stop audio when timer ends
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
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
    
    // Start background audio if enabled
    if (isAudioEnabled && audioRef.current) {
      // Reset audio to start
      audioRef.current.currentTime = 0;
      const playPromise = audioRef.current.play();
      
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            console.log("Audio started successfully");
          })
          .catch(error => {
            console.log("Audio play failed:", error);
            // Create a simple audio context for background tone
            createBackgroundTone();
          });
      }
    }
  };

  const createBackgroundTone = () => {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(220, audioContext.currentTime); // A3 note
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime); // Low volume
      
      oscillator.start();
      
      // Stop after 30 seconds or when game state changes
      setTimeout(() => {
        if (oscillator) {
          oscillator.stop();
          audioContext.close();
        }
      }, 30000);
      
    } catch (error) {
      console.log("Web Audio API not supported:", error);
    }
  };

  const toggleAudio = () => {
    setIsAudioEnabled(!isAudioEnabled);
    if (audioRef.current) {
      if (isAudioEnabled) {
        audioRef.current.pause();
      } else if (gameState === 'reading') {
        const playPromise = audioRef.current.play();
        if (playPromise !== undefined) {
          playPromise.catch(e => {
            console.log('Audio play failed:', e);
            createBackgroundTone();
          });
        }
      }
    }
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
      
      // Calculate new scoring system
      const correctAnswers = scoreData.correct_answers;
      const clausesIdentified = correctAnswers.length;
      
      // Calculate score out of 100 based on rarity
      let totalScore = 0;
      const scoreBreakdown = {};
      
      if (scoreData.legal_detector_breakdown) {
        Object.entries(scoreData.legal_detector_breakdown).forEach(([clauseId, data]) => {
          let points = 0;
          if (data.rarity === 'rare') {
            points = 30;
          } else if (data.rarity === 'moderate') {
            points = 20;
          } else {
            points = 15; // common
          }
          
          totalScore += points;
          scoreBreakdown[clauseId] = {
            ...data,
            points: points
          };
        });
      } else {
        // Fallback scoring if no breakdown available
        totalScore = clausesIdentified * 20; // 20 points per correct clause
      }
      
      const finalScore = {
        clausesIdentified: clausesIdentified,
        totalScore: Math.min(totalScore, 100), // Cap at 100
        maxScore: 100,
        breakdown: scoreBreakdown
      };

      setScore(finalScore);

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
      
      // Save result to localStorage
      const today = new Date().toISOString().split('T')[0];
      localStorage.setItem(`tc_auditor_${today}`, JSON.stringify({
        score: finalScore,
        userAnswers: answers,
        completedAt: new Date().toISOString()
      }));
      
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

  const getScoreDescription = (clausesFound) => {
    const descriptions = {
      5: "🕵️ Master Auditor - Nothing gets past you!",
      4: "📋 Senior Investigator - Sharp eye for shenanigans!",
      3: "🔍 Junior Detective - Getting warmer!",
      2: "📄 Intern Auditor - More coffee needed!",
      1: "🤷 Casual Clicker - Just like the rest of us!",
      0: "😅 Terms & Conditions Victim - Welcome to the club!"
    };
    return descriptions[clausesFound] || descriptions[0];
  };

  const generateShareText = () => {
    const description = getScoreDescription(score.clausesIdentified);
    return `🕵️ I audited today's Terms & Conditions in 30 seconds!
Found ${score.clausesIdentified}/5 absurd clauses hiding in the fine print.
Score: ${score.totalScore}/100 

${description}

Think you can spot the legal nonsense? 
Try your luck: tc-auditor.com

#FinePrintFinder #TermsAndConditions #LegalNonsense`;
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(generateShareText());
      toast({
        title: "📋 Copied!",
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

  const shareToWhatsApp = () => {
    const text = encodeURIComponent(generateShareText());
    window.open(`https://wa.me/?text=${text}`, '_blank');
  };

  if (loading && !currentGame) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center p-4">
        <div className="text-center text-white">
          <div className="relative">
            <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-cyan-300" />
            <div className="absolute inset-0 w-12 h-12 mx-auto mb-4 rounded-full bg-cyan-300/20 animate-pulse"></div>
          </div>
          <div className="text-lg font-medium">Loading today's audit...</div>
          <div className="text-sm text-gray-300 mt-2">Preparing your legal challenge</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-900 via-red-800 to-orange-900 flex items-center justify-center p-4">
        <div className="text-center text-white max-w-md">
          <XCircle className="w-16 h-16 mx-auto mb-4 text-red-300" />
          <div className="text-xl font-bold mb-2">Oops!</div>
          <div className="text-red-200 mb-6">{error}</div>
          <Button 
            onClick={() => window.location.reload()}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  if (!currentGame) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 text-white">
      {/* Background Audio */}
      <audio
        ref={audioRef}
        loop
        preload="auto"
        crossOrigin="anonymous"
      >
        <source src="data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmMcBDOHz+fUeSYEIHO+7OWYSgYPVK3j6KhVFApGnt8eoHMdBDOEze3YfSsEJXLH7eOYSgYPVqvm6ap3GQUJhs/j6KNZEAxQnuPx0GwjAy51zuHGeSYHKnf6xGE7ZSsBB2+c7OWFQAgOXavj5KhVFApEmt4ejoRtJD6FzuvYfSsFJXHG7uWSTS" type="audio/wav" />
      </audio>

      {/* Welcome State */}
      {gameState === 'welcome' && !hasPlayedToday && (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
          <div className="text-center mb-8">
            <div className="relative mb-8">
              <h1 className="text-6xl md:text-8xl font-black bg-gradient-to-r from-cyan-300 via-blue-300 to-purple-300 bg-clip-text text-transparent mb-4 animate-pulse">
                T&C Auditor
              </h1>
              <div className="absolute -top-2 -right-2 w-8 h-8 bg-yellow-400 rounded-full animate-bounce">
                <Zap className="w-5 h-5 text-yellow-900 m-1.5" />
              </div>
            </div>
            
            <p className="text-xl md:text-2xl text-gray-300 mb-8 leading-relaxed">
              The daily legal challenge that tests your ability to spot absurd clauses
            </p>
            
            <div className="text-center mb-8">
              <Button 
                onClick={startGame}
                size="lg"
                className="text-xl md:text-2xl px-8 py-6 md:px-12 md:py-8 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 transform hover:scale-105 transition-all duration-300 shadow-2xl shadow-cyan-500/25 rounded-2xl font-bold border-2 border-cyan-400/50"
              >
                🔍 Expose the Fine Print
              </Button>
              {currentGame && (
                <p className="text-sm text-gray-400 mt-3 italic">
                  Today's Challenge: {currentGame.title}
                </p>
              )}
            </div>
            
            <div className="bg-black/30 backdrop-blur-sm rounded-2xl p-6 shadow-2xl border border-purple-500/30">
              <h2 className="text-2xl md:text-3xl font-bold mb-6 text-cyan-300">⚡ How to Play</h2>
              <div className="grid md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-blue-600/30 to-cyan-600/30 rounded-xl p-4 backdrop-blur-sm border border-cyan-500/30">
                  <div className="flex items-center justify-center space-x-3 mb-3">
                    <div className="w-10 h-10 bg-cyan-400 rounded-full flex items-center justify-center">
                      <Timer className="w-5 h-5 text-cyan-900" />
                    </div>
                    <span className="font-bold text-lg">1. Speed Read</span>
                  </div>
                  <p className="text-sm text-gray-300">Scan the T&C document for 30 intense seconds</p>
                </div>
                <div className="bg-gradient-to-br from-green-600/30 to-emerald-600/30 rounded-xl p-4 backdrop-blur-sm border border-emerald-500/30">
                  <div className="flex items-center justify-center space-x-3 mb-3">
                    <div className="w-10 h-10 bg-emerald-400 rounded-full flex items-center justify-center">
                      <Target className="w-5 h-5 text-emerald-900" />
                    </div>
                    <span className="font-bold text-lg">2. Identify</span>
                  </div>
                  <p className="text-sm text-gray-300">Select 5 clauses that were actually in the document</p>
                </div>
                <div className="bg-gradient-to-br from-yellow-600/30 to-orange-600/30 rounded-xl p-4 backdrop-blur-sm border border-yellow-500/30">
                  <div className="flex items-center justify-center space-x-3 mb-3">
                    <div className="w-10 h-10 bg-yellow-400 rounded-full flex items-center justify-center">
                      <Trophy className="w-5 h-5 text-yellow-900" />
                    </div>
                    <span className="font-bold text-lg">3. Score</span>
                  </div>
                  <p className="text-sm text-gray-300">Get your Legal Detector score and share!</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Already Played Today - Redirect to Results */}
      {gameState === 'welcome' && hasPlayedToday && (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
          <div className="text-center">
            <Trophy className="w-16 h-16 mx-auto mb-4 text-yellow-400" />
            <h1 className="text-4xl font-bold mb-4">Welcome Back!</h1>
            <p className="text-xl text-gray-300 mb-8">You've already completed today's challenge</p>
            <Button 
              onClick={() => setGameState('results')}
              size="lg"
              className="text-xl px-8 py-6 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 transform hover:scale-105 transition-all duration-300"
            >
              View Your Results 🏆
            </Button>
          </div>
        </div>
      )}

      {/* Reading State */}
      {gameState === 'reading' && (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
          <div className="mb-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h2 className="text-2xl md:text-3xl font-bold text-cyan-300">⚡ Speed Reading Phase</h2>
                <p className="text-sm text-gray-400 italic">Auditing: {currentGame.title}</p>
              </div>
              <div className="flex items-center space-x-4">
                <Button
                  onClick={toggleAudio}
                  variant="outline"
                  size="sm"
                  className="bg-black/30 border-purple-500/50 text-white hover:bg-purple-600/30"
                >
                  {isAudioEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
                </Button>
                <div className={`flex items-center space-x-2 ${timeLeft <= 10 ? 'animate-pulse text-red-400' : 'text-cyan-300'}`}>
                  <Clock className="w-6 h-6" />
                  <span className="text-3xl md:text-4xl font-bold">{timeLeft}s</span>
                </div>
              </div>
            </div>
            <Progress 
              value={(30 - timeLeft) / 30 * 100} 
              className={`h-3 ${timeLeft <= 10 ? 'animate-pulse' : ''}`} 
            />
            <p className="text-sm text-gray-300 mt-2">
              🔍 Scan for absurd, unusual, or suspicious clauses. You'll be tested on them!
            </p>
          </div>

          <Card className="bg-black/40 border-purple-500/30 backdrop-blur-sm shadow-2xl">
            <CardHeader className="bg-gradient-to-r from-purple-600/30 to-pink-600/30">
              <CardTitle className="text-lg text-white">{currentGame.title}</CardTitle>
            </CardHeader>
            <CardContent className="h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-purple-600 scrollbar-track-transparent">
              <div className="whitespace-pre-line text-xs leading-tight text-gray-200 p-4 font-mono">
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
            <div>
              <h2 className="text-2xl md:text-3xl font-bold mb-2 text-cyan-300">🎯 Clause Identification</h2>
              <p className="text-sm text-gray-400 italic mb-2">Auditing: {currentGame.title}</p>
            </div>
            <p className="text-gray-300 mb-4">
              Select exactly 5 clauses that were actually present in the document you just read.
            </p>
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4 bg-black/30 rounded-xl p-4 backdrop-blur-sm border border-purple-500/30">
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-300">
                  Selected: <span className="font-bold text-cyan-300">{selectedClauses.length}/5</span>
                </span>
                <div className="flex space-x-1">
                  {[...Array(5)].map((_, i) => (
                    <div 
                      key={i} 
                      className={`w-3 h-3 rounded-full ${i < selectedClauses.length ? 'bg-cyan-400' : 'bg-gray-600'}`}
                    />
                  ))}
                </div>
              </div>
              <Button 
                onClick={submitQuiz}
                disabled={selectedClauses.length !== 5 || loading}
                className={`px-6 py-3 font-bold rounded-xl transition-all duration-300 ${
                  selectedClauses.length === 5 
                    ? 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 transform hover:scale-105 shadow-lg shadow-green-500/25' 
                    : 'bg-gray-600 cursor-not-allowed opacity-50'
                }`}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  '🚀 Submit Audit'
                )}
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
                  className={`cursor-pointer transition-all duration-300 transform hover:scale-[1.02] ${
                    isSelected 
                      ? 'ring-2 ring-cyan-400 bg-gradient-to-r from-cyan-900/40 to-blue-900/40 shadow-lg shadow-cyan-500/20 border-cyan-400/50' 
                      : 'bg-black/30 hover:bg-black/50 border-purple-500/30 hover:border-purple-400/50'
                  } backdrop-blur-sm`}
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
                      <Badge 
                        variant="outline" 
                        className={`mt-1 font-bold text-lg px-3 py-1 ${
                          isSelected 
                            ? 'bg-cyan-400 text-cyan-900 border-cyan-300' 
                            : 'bg-purple-600/30 text-purple-200 border-purple-400'
                        }`}
                      >
                        {String.fromCharCode(65 + index)}
                      </Badge>
                      <p className="text-xs flex-1 text-gray-200 leading-tight font-mono">{clause.text}</p>
                      {isSelected && (
                        <div className="animate-bounce">
                          <CheckCircle className="w-6 h-6 text-cyan-400" />
                        </div>
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
            <div className="relative">
              <h2 className="text-3xl md:text-4xl font-bold mb-2 text-cyan-300">🏆 Audit Complete!</h2>
              <p className="text-sm text-gray-400 italic mb-6">Final report: {currentGame.title}</p>
              <div className="absolute -top-2 -right-2 w-8 h-8 bg-yellow-400 rounded-full animate-bounce">
                <Trophy className="w-5 h-5 text-yellow-900 m-1.5" />
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-black/50 to-purple-900/30 rounded-2xl p-8 shadow-2xl mb-8 backdrop-blur-sm border border-purple-500/30">
              <div className="mb-6">
                <div className="text-2xl md:text-3xl text-cyan-300 font-bold mb-2">
                  {score.clausesIdentified} Clauses Identified
                </div>
                <div className="text-6xl md:text-8xl font-black bg-gradient-to-r from-cyan-300 via-blue-300 to-purple-300 bg-clip-text text-transparent score-reveal">
                  {score.totalScore}
                </div>
                <div className="text-xl md:text-2xl text-gray-300 font-bold mb-4">Score out of 100</div>
                
                {/* Interactive Score Description */}
                <div className="bg-black/40 rounded-xl p-4 mb-6 border border-cyan-500/30">
                  <div className="text-cyan-300 font-bold text-lg md:text-xl text-center animate-pulse">
                    {getScoreDescription(score.clausesIdentified)}
                  </div>
                </div>
              </div>
              
              {score.breakdown && Object.keys(score.breakdown).length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {Object.entries(score.breakdown).map(([clauseId, data]) => (
                    <div key={clauseId} className="bg-black/30 rounded-lg p-3 border border-purple-500/30">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-gray-300 text-sm">Clause {clauseId.replace('rac', '')}</span>
                        <span className={`font-bold px-2 py-1 rounded text-xs ${
                          data.rarity === 'rare' ? 'bg-red-600/30 text-red-300' :
                          data.rarity === 'moderate' ? 'bg-yellow-600/30 text-yellow-300' :
                          'bg-green-600/30 text-green-300'
                        }`}>
                          {data.rarity}
                        </span>
                      </div>
                      <div className="text-purple-300 font-bold text-lg">+{data.points} pts</div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Countdown to tomorrow */}
              <div className="bg-black/40 rounded-xl p-4 mt-6 border border-yellow-500/30">
                <div className="text-yellow-300 font-bold mb-2">⏱️ Next Challenge In:</div>
                <div className="text-2xl md:text-3xl font-mono font-bold text-yellow-400">{countdown}</div>
              </div>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
              <Button 
                onClick={copyToClipboard} 
                variant="outline" 
                className="bg-black/30 border-purple-500/50 text-white hover:bg-purple-600/30 backdrop-blur-sm"
              >
                <Copy className="w-4 h-4 mr-2" />
                📋 Copy Results
              </Button>
              <Button 
                onClick={shareToTwitter} 
                variant="outline" 
                className="bg-black/30 border-blue-500/50 text-white hover:bg-blue-600/30 backdrop-blur-sm"
              >
                <Share2 className="w-4 h-4 mr-2" />
                🐦 Share on X
              </Button>
              <Button 
                onClick={shareToWhatsApp} 
                variant="outline" 
                className="bg-black/30 border-green-500/50 text-white hover:bg-green-600/30 backdrop-blur-sm"
              >
                <Share2 className="w-4 h-4 mr-2" />
                💬 WhatsApp
              </Button>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <h3 className="text-xl md:text-2xl font-bold mb-2 text-cyan-300">📜 Today's Real Absurd Clauses</h3>
              <p className="text-sm text-gray-400 italic mb-4">Hidden in: {currentGame.title}</p>
            </div>
            {currentGame.real_absurd_clauses.map((clause, index) => (
              <Card key={clause.id} className="bg-gradient-to-r from-green-900/40 to-emerald-900/40 border-green-400/50 backdrop-blur-sm">
                <CardContent className="p-4">
                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 bg-green-400 rounded-full flex items-center justify-center">
                      <CheckCircle className="w-5 h-5 text-green-900" />
                    </div>
                    <div>
                      <div className="text-xs text-green-300 font-bold mb-1">Real Clause #{index + 1}</div>
                      <p className="text-xs text-gray-200 leading-tight font-mono">{clause.text}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="text-center mt-8">
            <Button 
              onClick={() => {
                setGameState('welcome');
                setHasPlayedToday(false);
              }}
              variant="outline"
              className="bg-black/30 border-purple-500/50 text-white hover:bg-purple-600/30 backdrop-blur-sm px-8 py-3"
            >
              🔄 Play Demo Again
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TCAuditorGame;