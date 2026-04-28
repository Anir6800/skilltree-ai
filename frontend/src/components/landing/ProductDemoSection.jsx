/**
 * ProductDemoSection Component
 * Interactive in-page product tour with clickable skill tree and quest preview
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Play, Check, Lock } from 'lucide-react';
import useScrollAnimation from '../../hooks/useScrollAnimation';

const ProductDemoSection = () => {
  const [selectedNode, setSelectedNode] = useState('arrays');
  const [activeTab, setActiveTab] = useState('problem');
  const [hasRun, setHasRun] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [typewriterText, setTypewriterText] = useState('');
  const { ref, className } = useScrollAnimation({ threshold: 0.2 });

  const nodes = [
    { id: 'arrays', label: 'Arrays', status: 'completed', x: 50, y: 50 },
    { id: 'linked-lists', label: 'Linked Lists', status: 'locked', x: 150, y: 50 },
    { id: 'two-pointers', label: 'Two Pointers', status: 'available', x: 50, y: 150 },
    { id: 'sliding-window', label: 'Sliding Window', status: 'locked', x: 150, y: 150 },
    { id: 'binary-search', label: 'Binary Search', status: 'available', x: 100, y: 250 },
    { id: 'dynamic-programming', label: 'Dynamic Programming', status: 'locked', x: 200, y: 250 },
  ];

  const edges = [
    { from: 'arrays', to: 'linked-lists' },
    { from: 'arrays', to: 'two-pointers' },
    { from: 'two-pointers', to: 'sliding-window' },
    { from: 'two-pointers', to: 'binary-search' },
    { from: 'sliding-window', to: 'dynamic-programming' },
  ];

  const questData = {
    arrays: {
      title: 'Two Sum',
      description: 'Given an array of integers nums and an integer target, return indices of the two numbers that add up to target.',
      examples: [
        { input: 'nums = [2,7,11,15], target = 9', output: '[0,1]' },
        { input: 'nums = [3,2,4], target = 6', output: '[1,2]' },
      ],
      starterCode: `def two_sum(nums, target):
    """
    Find two numbers that add up to target.
    
    Args:
        nums: List of integers
        target: Target sum
    
    Returns:
        List of two indices
    """
    # Your code here
    pass`,
      feedback: 'Great work! Your solution correctly uses a hash map to achieve O(n) time complexity. The logic is clean and handles edge cases well. Consider adding input validation for empty arrays.',
    },
    'two-pointers': {
      title: 'Container With Most Water',
      description: 'Given n non-negative integers representing heights, find two lines that together with the x-axis form a container with the most water.',
      examples: [
        { input: 'height = [1,8,6,2,5,4,8,3,7]', output: '49' },
        { input: 'height = [1,1]', output: '1' },
      ],
      starterCode: `def max_area(height):
    """
    Find maximum water container area.
    
    Args:
        height: List of heights
    
    Returns:
        Maximum area
    """
    # Your code here
    pass`,
      feedback: 'Excellent two-pointer approach! You correctly move the pointer with the smaller height, achieving O(n) time. The solution is optimal. Minor suggestion: add a comment explaining why we move the smaller pointer.',
    },
    'binary-search': {
      title: 'Search in Rotated Sorted Array',
      description: 'Given a rotated sorted array and a target value, return the index of the target if found, otherwise return -1.',
      examples: [
        { input: 'nums = [4,5,6,7,0,1,2], target = 0', output: '4' },
        { input: 'nums = [4,5,6,7,0,1,2], target = 3', output: '-1' },
      ],
      starterCode: `def search(nums, target):
    """
    Search for target in rotated sorted array.
    
    Args:
        nums: Rotated sorted array
        target: Target value
    
    Returns:
        Index of target or -1
    """
    # Your code here
    pass`,
      feedback: 'Strong binary search implementation! You correctly identify which half is sorted and adjust the search space. Time complexity O(log n) is optimal. Consider edge case: what if the array has duplicates?',
    },
  };

  const currentQuest = questData[selectedNode] || questData.arrays;

  const handleNodeClick = (nodeId, status) => {
    if (status === 'locked') return;
    setSelectedNode(nodeId);
    setActiveTab('problem');
    setHasRun(false);
    setTypewriterText('');
  };

  const handleRunDemo = () => {
    setIsRunning(true);
    setTimeout(() => {
      setIsRunning(false);
      setHasRun(true);
      setActiveTab('feedback');
    }, 1200);
  };

  useEffect(() => {
    if (activeTab === 'feedback' && hasRun && typewriterText.length < currentQuest.feedback.length) {
      const timeout = setTimeout(() => {
        setTypewriterText(currentQuest.feedback.slice(0, typewriterText.length + 1));
      }, 20);
      return () => clearTimeout(timeout);
    }
  }, [activeTab, hasRun, typewriterText, currentQuest.feedback]);

  useEffect(() => {
    if (activeTab === 'feedback' && hasRun) {
      setTypewriterText('');
    }
  }, [activeTab, hasRun]);

  const getNodeStyle = (status) => {
    const baseStyle = 'transition-all duration-300';
    switch (status) {
      case 'completed':
        return `${baseStyle} fill-green-500/10 stroke-green-500 stroke-2`;
      case 'available':
        return `${baseStyle} fill-purple-500/10 stroke-purple-500 stroke-2 cursor-pointer hover:fill-purple-500/20`;
      case 'locked':
        return `${baseStyle} fill-gray-500/10 stroke-gray-500 stroke-2 cursor-not-allowed`;
      default:
        return baseStyle;
    }
  };

  const getNodeIcon = (status) => {
    switch (status) {
      case 'completed':
        return <Check size={16} className="text-green-500" />;
      case 'locked':
        return <Lock size={16} className="text-gray-500" />;
      default:
        return null;
    }
  };

  return (
    <section
      id="product-demo"
      ref={ref}
      className={`relative py-24 px-6 bg-[#0a0c10] ${className} animate-in-default`}
    >
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm mb-4">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              ✦ SEE IT IN ACTION
            </span>
          </div>
          <h2 className="text-5xl font-black tracking-tighter mb-4 text-white">
            Experience it before you sign up
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            Click a skill. Try a quest. See AI feedback — all without an account.
          </p>
        </div>

        {/* Demo Layout */}
        <div className="grid lg:grid-cols-[40%_60%] gap-8 mb-12">
          {/* Left Column: Mini Skill Tree */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-8 backdrop-blur-sm">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-6">
              Your Skill Path
            </h3>
            <svg viewBox="0 0 300 350" className="w-full h-auto">
              {/* Edges */}
              {edges.map((edge, idx) => {
                const fromNode = nodes.find((n) => n.id === edge.from);
                const toNode = nodes.find((n) => n.id === edge.to);
                return (
                  <line
                    key={idx}
                    x1={fromNode.x + 40}
                    y1={fromNode.y + 40}
                    x2={toNode.x + 40}
                    y2={toNode.y + 40}
                    stroke="rgba(124, 106, 245, 0.3)"
                    strokeWidth="2"
                    strokeDasharray="5,5"
                    className="animate-dash"
                  />
                );
              })}

              {/* Nodes */}
              {nodes.map((node) => (
                <g
                  key={node.id}
                  onClick={() => handleNodeClick(node.id, node.status)}
                  className={node.status === 'locked' ? '' : 'cursor-pointer'}
                >
                  <circle
                    cx={node.x + 40}
                    cy={node.y + 40}
                    r="35"
                    className={getNodeStyle(node.status)}
                  />
                  <foreignObject x={node.x + 10} y={node.y + 10} width="60" height="60">
                    <div className="flex flex-col items-center justify-center h-full text-center">
                      {getNodeIcon(node.status)}
                      <span className="text-[10px] font-semibold text-white mt-1 leading-tight">
                        {node.label}
                      </span>
                    </div>
                  </foreignObject>
                  {selectedNode === node.id && node.status !== 'locked' && (
                    <circle
                      cx={node.x + 40}
                      cy={node.y + 40}
                      r="38"
                      fill="none"
                      stroke="#7c6af5"
                      strokeWidth="3"
                      className="animate-pulse"
                    />
                  )}
                </g>
              ))}
            </svg>
          </div>

          {/* Right Column: Quest Preview */}
          <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden backdrop-blur-sm">
            {/* Tab Strip */}
            <div className="flex border-b border-white/10">
              {['problem', 'code', 'feedback'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  disabled={tab === 'feedback' && !hasRun}
                  className={`flex-1 px-6 py-4 text-sm font-semibold uppercase tracking-wider transition-all ${
                    activeTab === tab
                      ? 'bg-white/10 text-white border-b-2 border-purple-500'
                      : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
                  } ${tab === 'feedback' && !hasRun ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="p-8">
              {activeTab === 'problem' && (
                <div>
                  <h3 className="text-2xl font-bold text-white mb-4">{currentQuest.title}</h3>
                  <p className="text-slate-300 mb-6 leading-relaxed">{currentQuest.description}</p>
                  <div className="space-y-4">
                    {currentQuest.examples.map((example, idx) => (
                      <div key={idx} className="bg-black/30 rounded-lg p-4 border border-white/5">
                        <div className="text-xs font-mono text-slate-400 mb-2">Example {idx + 1}</div>
                        <div className="space-y-2">
                          <div>
                            <span className="text-xs font-semibold text-slate-500 uppercase">Input:</span>
                            <div className="text-sm font-mono text-green-400 mt-1">{example.input}</div>
                          </div>
                          <div>
                            <span className="text-xs font-semibold text-slate-500 uppercase">Output:</span>
                            <div className="text-sm font-mono text-cyan-400 mt-1">{example.output}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'code' && (
                <div>
                  <div className="bg-[#1e1e1e] rounded-lg p-6 mb-4 border border-white/5">
                    <pre className="text-sm font-mono text-slate-300 overflow-x-auto">
                      <code>{currentQuest.starterCode}</code>
                    </pre>
                  </div>
                  <button
                    onClick={handleRunDemo}
                    disabled={isRunning}
                    className="flex items-center space-x-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Play size={16} />
                    <span>{isRunning ? 'Running...' : 'Run Demo ▶'}</span>
                  </button>
                  {hasRun && (
                    <div className="mt-4 bg-green-500/10 border border-green-500/30 rounded-lg p-4 animate-in-default animate-in">
                      <div className="flex items-center space-x-2 text-green-400">
                        <Check size={20} />
                        <span className="font-semibold">✓ 3/3 tests passed · 42ms</span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'feedback' && hasRun && (
                <div>
                  <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-6 mb-4">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-bold text-white">AI Evaluation</h4>
                      <div className="text-2xl font-black text-purple-400">87/100</div>
                    </div>
                    <div className="text-slate-300 leading-relaxed font-mono text-sm min-h-[100px]">
                      {typewriterText}
                      {typewriterText.length < currentQuest.feedback.length && (
                        <span className="inline-block w-2 h-4 bg-purple-400 ml-1 animate-pulse" />
                      )}
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-black/30 rounded-lg p-4 border border-white/5">
                      <div className="text-xs font-semibold text-slate-500 uppercase mb-2">Time Complexity</div>
                      <div className="text-lg font-mono text-cyan-400">O(n)</div>
                    </div>
                    <div className="bg-black/30 rounded-lg p-4 border border-white/5">
                      <div className="text-xs font-semibold text-slate-500 uppercase mb-2">Space Complexity</div>
                      <div className="text-lg font-mono text-cyan-400">O(n)</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="text-center">
          <p className="text-slate-400 mb-6">
            This is just a preview. Your real path has <span className="text-white font-semibold">50+ skills</span> and{' '}
            <span className="text-white font-semibold">180+ quests</span>.
          </p>
          <Link
            to="/register"
            className="inline-block px-8 py-4 bg-gradient-to-r from-purple-600 to-cyan-600 text-white font-bold rounded-lg hover:shadow-[0_0_30px_rgba(124,106,245,0.5)] transition-all"
          >
            Build My Path →
          </Link>
        </div>
      </div>

      <style jsx>{`
        @keyframes dash {
          to {
            stroke-dashoffset: -10;
          }
        }

        .animate-dash {
          animation: dash 1s linear infinite;
        }
      `}</style>
    </section>
  );
};

export default ProductDemoSection;
