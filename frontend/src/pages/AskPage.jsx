import React, { useState } from 'react';
import { Bot, User, Code, AlertTriangle, Command } from 'lucide-react';
import api from '../api/client';

const EXAMPLE_QUESTIONS = {
  en: [
    'Which country imported the most boron in 2022?',
    'Show me price anomalies after 2015',
    'Which countries are most dependent on Turkish boron?',
    'How did exports change after the 2019 facility expansion?'
  ],
  tr: [
    '2022 yilinda en fazla boron ithal eden ulke hangisi?',
    '2015 sonrasi fiyat anomalilerini goster',
    'Turk boronuna en bagimli ulkeler hangileri?',
    'Kirka genislemesinden sonra ihracat nasil degisti?'
  ]
};

const AskPage = () => {
    const [lang, setLang] = useState('en');
    const [question, setQuestion] = useState('');
    const [activeResponse, setActiveResponse] = useState(null);
    const [history, setHistory] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showQuery, setShowQuery] = useState(false);

    const handleSubmit = async (e) => {
        if (e) e.preventDefault();
        if (!question.trim() || isLoading) return;

        setIsLoading(true);
        setError(null);

        try {
            const res = await api.post('/nl-query', { question });
            
            const newResp = {
                question: question,
                answer: res.data.answer,
                path: res.data.path,
                queryText: res.data.query,
                timestamp: new Date().toLocaleTimeString()
            };

            // Shift history down
            if (activeResponse) {
                setHistory(prev => [activeResponse, ...prev].slice(0, 5));
            }
            
            setActiveResponse(newResp);
            setShowQuery(false);
            setQuestion('');
            
        } catch (err) {
            console.error(err);
            if (err.response?.status === 503) {
                setError('Natural language queries are not available in this environment. (GEMINI_API_KEY missing)');
            } else {
                setError('An error occurred interpreting your question. Please try rephrasing.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const getBadgeProps = (pathStr) => {
        if(pathStr === 'sql') return { label: 'SQL', color: 'bg-blue-100 text-blue-800 border-blue-200' };
        if(pathStr === 'cypher') return { label: 'GRAPH', color: 'bg-green-100 text-green-800 border-green-200' };
        return { label: 'DIRECT', color: 'bg-gray-100 text-gray-800 border-gray-200' };
    };

    return (
        <div className="max-w-4xl mx-auto p-4 md:p-6 space-y-6">
            
            {/* Header & Language Toggle */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b pb-4">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2 text-gray-800">
                        <Command className="w-8 h-8 text-primary-600" />
                        Ask BorAnalytics
                    </h1>
                    <p className="text-gray-500 mt-1">Ask any question about the global boron trade network using natural language.</p>
                </div>
                
                <div className="flex bg-gray-100 p-1 rounded-lg border">
                    <button 
                        onClick={() => setLang('en')}
                        className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${lang === 'en' ? 'bg-white shadow text-primary-700' : 'text-gray-500'}`}
                    >
                        EN
                    </button>
                    <button 
                        onClick={() => setLang('tr')}
                        className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${lang === 'tr' ? 'bg-white shadow text-primary-700' : 'text-gray-500'}`}
                    >
                        TR
                    </button>
                </div>
            </div>

            {/* Error Banner */}
            {error && (
                <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-md flex gap-3 text-red-700">
                    <AlertTriangle className="h-5 w-5 shrink-0" />
                    <p>{error}</p>
                </div>
            )}

            {/* Application Console */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
                
                {/* Scrollable Conversation View */}
                <div className="flex-1 p-6 flex flex-col gap-6" style={{ minHeight: '40vh' }}>
                    
                    {/* Empty State / Suggestions */}
                    {!activeResponse && history.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-full text-center space-y-6 opacity-75 mt-8">
                            <Bot className="w-16 h-16 text-gray-300" />
                            <div className="space-y-3">
                                {EXAMPLE_QUESTIONS[lang].map((q, i) => (
                                    <button 
                                        key={i} 
                                        onClick={() => setQuestion(q)}
                                        className="block w-full text-left px-4 py-2 bg-gray-50 hover:bg-primary-50 hover:text-primary-700 border rounded-lg transition-colors text-sm"
                                    >
                                        "{q}"
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Active Conversation Response */}
                    {activeResponse && (
                        <div className="space-y-6">
                            {/* User Question Bubble */}
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center shrink-0">
                                    <User className="w-4 h-4 text-gray-600" />
                                </div>
                                <div className="flex-1 pt-1">
                                    <p className="font-medium text-gray-800 text-lg">{activeResponse.question}</p>
                                </div>
                            </div>

                            {/* AI Answer Bubble */}
                            <div className="flex items-start gap-4 bg-primary-50/30 p-4 rounded-xl border border-primary-100">
                                <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
                                    <Bot className="w-4 h-4 text-primary-700" />
                                </div>
                                <div className="flex-1 space-y-4">
                                    <div className="prose prose-blue text-gray-700 leading-relaxed">
                                        {activeResponse.answer}
                                    </div>
                                    
                                    <div className="flex items-center justify-between pt-2">
                                        <span className={`text-xs px-2 py-1 rounded-full border font-bold ${getBadgeProps(activeResponse.path).color}`}>
                                            {getBadgeProps(activeResponse.path).label} ROUTER
                                        </span>
                                        
                                        {activeResponse.queryText && (
                                            <button 
                                                onClick={() => setShowQuery(!showQuery)}
                                                className="text-xs text-primary-600 hover:text-primary-800 flex items-center gap-1 font-medium"
                                            >
                                                <Code className="w-3 h-3" />
                                                {showQuery ? 'Hide Query' : 'View Query'}
                                            </button>
                                        )}
                                    </div>

                                    {showQuery && activeResponse.queryText && (
                                        <div className="bg-gray-800 rounded-lg p-3 text-sm text-green-400 font-mono overflow-x-auto">
                                            <pre>{activeResponse.queryText}</pre>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Input Area strictly pinned bottom */}
                <div className="p-4 bg-gray-50 border-t">
                    <form onSubmit={handleSubmit} className="relative flex items-center">
                        <input
                            type="text"
                            value={question}
                            onChange={(e) => setQuestion(e.target.value)}
                            disabled={isLoading}
                            placeholder={lang === 'en' ? "Ask a question about boron trade..." : "Boron ticareti hakkinda soru sorun..."}
                            className="w-full pl-4 pr-24 py-3 rounded-lg border focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:opacity-50 shadow-sm"
                        />
                        <button
                            type="submit"
                            disabled={!question.trim() || isLoading}
                            className="absolute right-2 px-4 py-1.5 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {isLoading ? 'Thinking...' : 'Send'}
                        </button>
                    </form>
                </div>
            </div>

            {/* Conversation History Stack */}
            {history.length > 0 && (
                <div className="mt-8">
                    <h3 className="text-sm font-bold text-gray-500 mb-4 uppercase tracking-wider">Previous Questions</h3>
                    <div className="space-y-4">
                        {history.map((item, idx) => (
                            <div key={idx} className="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
                                <div className="flex items-center gap-2 mb-2">
                                    <User className="w-3 h-3 text-gray-400" />
                                    <span className="font-medium text-gray-700 text-sm">{item.question}</span>
                                    <span className="ml-auto text-xs text-gray-400">{item.timestamp}</span>
                                </div>
                                <div className="pl-5 border-l-2 border-primary-100">
                                    <p className="text-gray-600 text-sm leading-relaxed line-clamp-2">{item.answer}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
            
        </div>
    );
};

export default AskPage;
