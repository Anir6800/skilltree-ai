/**
 * SkillTree AI - Solutions Page
 * Peer code review system with shared solutions, comments, and diff viewer.
 */

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Editor from '@monaco-editor/react';
import {
  ThumbsUp, MessageCircle, Eye, Clock, Code2, User,
  ChevronDown, ChevronUp, Send, Trash2, Reply, X,
  Loader2, AlertCircle, Share2,
} from 'lucide-react';
import {
  getSolutions,
  getSolutionDetail,
  getSolutionDiff,
  toggleUpvote,
  addComment,
  deleteComment,
} from '../api/solutionsApi';
import { cn } from '../utils/cn';
import useAuthStore from '../store/authStore';
import MainLayout from '../components/layout/MainLayout';

const LANGUAGE_COLORS = {
  python: { bg: 'bg-blue-500/20', border: 'border-blue-500/40', text: 'text-blue-400' },
  javascript: { bg: 'bg-yellow-500/20', border: 'border-yellow-500/40', text: 'text-yellow-400' },
  cpp: { bg: 'bg-cyan-500/20', border: 'border-cyan-500/40', text: 'text-cyan-400' },
  java: { bg: 'bg-orange-500/20', border: 'border-orange-500/40', text: 'text-orange-400' },
  go: { bg: 'bg-teal-500/20', border: 'border-teal-500/40', text: 'text-teal-400' },
};

function SolutionCard({ solution, onViewDetail, isSelected }) {
  const langColor = LANGUAGE_COLORS[solution.language] || LANGUAGE_COLORS.python;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'p-4 rounded-lg border transition-all cursor-pointer',
        isSelected
          ? 'bg-primary/10 border-primary/50 shadow-lg shadow-primary/20'
          : 'bg-white/5 border-white/10 hover:bg-white/8 hover:border-white/20'
      )}
      onClick={() => onViewDetail(solution)}
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {solution.user_avatar && (
            <img
              src={solution.user_avatar}
              alt={solution.user_username}
              className="w-8 h-8 rounded-full border border-white/20"
            />
          )}
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-white truncate">
              {solution.is_anonymous ? 'Anonymous' : solution.user_username}
            </p>
            <p className="text-xs text-slate-400">Level {solution.user_level}</p>
          </div>
        </div>
        <span className={cn('px-2 py-1 rounded text-xs font-bold', langColor.bg, langColor.border, 'border', langColor.text)}>
          {solution.language.toUpperCase()}
        </span>
      </div>

      <p className="text-sm text-slate-300 mb-3 line-clamp-2">{solution.quest_title}</p>

      <div className="flex items-center justify-between text-xs text-slate-400 mb-3">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <Code2 size={14} />
            {solution.code_line_count} lines
          </span>
          <span className="flex items-center gap-1">
            <Clock size={14} />
            {solution.solve_time_minutes}m
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-white/10">
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1 text-slate-400">
            <ThumbsUp size={14} className={solution.user_upvoted ? 'fill-primary text-primary' : ''} />
            {solution.upvote_count}
          </span>
          <span className="flex items-center gap-1 text-slate-400">
            <MessageCircle size={14} />
            {solution.comment_count}
          </span>
          <span className="flex items-center gap-1 text-slate-400">
            <Eye size={14} />
            {solution.views_count}
          </span>
        </div>
        <span className="text-xs text-slate-500">
          {new Date(solution.shared_at).toLocaleDateString()}
        </span>
      </div>
    </motion.div>
  );
}

function CommentThread({ comment, onReply, onDelete, currentUserId, depth = 0 }) {
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmitReply = async () => {
    if (!replyText.trim()) return;
    setIsSubmitting(true);
    try {
      await onReply(replyText, comment.id);
      setReplyText('');
      setShowReplyForm(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      className={cn('mb-4', depth > 0 && 'ml-6 pl-4 border-l border-white/10')}
    >
      <div className="flex gap-3">
        {comment.author_avatar && (
          <img
            src={comment.author_avatar}
            alt={comment.author_username}
            className="w-8 h-8 rounded-full border border-white/20 flex-shrink-0"
          />
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-semibold text-white">{comment.author_username}</span>
            <span className="text-xs text-slate-500">Level {comment.author_level}</span>
            <span className="text-xs text-slate-600">
              {new Date(comment.created_at).toLocaleDateString()}
            </span>
          </div>
          <p className="text-sm text-slate-300 mb-2 break-words">{comment.text}</p>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowReplyForm(!showReplyForm)}
              className="flex items-center gap-1 text-xs text-slate-400 hover:text-primary transition-colors"
            >
              <Reply size={14} />
              Reply
            </button>
            {currentUserId === comment.author_username && (
              <button
                onClick={() => onDelete(comment.id)}
                className="flex items-center gap-1 text-xs text-slate-400 hover:text-red-400 transition-colors"
              >
                <Trash2 size={14} />
                Delete
              </button>
            )}
          </div>

          {showReplyForm && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-3 flex gap-2"
            >
              <input
                type="text"
                placeholder="Write a reply..."
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                maxLength={1000}
                className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary/50"
              />
              <button
                onClick={handleSubmitReply}
                disabled={isSubmitting || !replyText.trim()}
                className="px-3 py-2 bg-primary/20 border border-primary/40 rounded text-sm font-semibold text-primary hover:bg-primary/30 disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              </button>
            </motion.div>
          )}
        </div>
      </div>

      {comment.replies && comment.replies.length > 0 && (
        <div className="mt-4">
          {comment.replies.map((reply) => (
            <CommentThread
              key={reply.id}
              comment={reply}
              onReply={onReply}
              onDelete={onDelete}
              currentUserId={currentUserId}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </motion.div>
  );
}

function SolutionViewer({ solution, onClose }) {
  const [showDiff, setShowDiff] = useState(false);
  const [diffData, setDiffData] = useState(null);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [isLoadingDiff, setIsLoadingDiff] = useState(false);
  const [isSubmittingComment, setIsSubmittingComment] = useState(false);
  const [isUpvoting, setIsUpvoting] = useState(false);
  const { user } = useAuthStore();
  const langColor = LANGUAGE_COLORS[solution.language] || LANGUAGE_COLORS.python;

  useEffect(() => {
    setComments(solution.comments || []);
  }, [solution]);

  const handleToggleDiff = async () => {
    if (showDiff) {
      setShowDiff(false);
      return;
    }

    if (!diffData) {
      setIsLoadingDiff(true);
      try {
        const data = await getSolutionDiff(solution.id);
        setDiffData(data);
      } catch (err) {
        console.error('Failed to load diff:', err);
      } finally {
        setIsLoadingDiff(false);
      }
    }
    setShowDiff(true);
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    setIsSubmittingComment(true);
    try {
      const comment = await addComment(solution.id, newComment);
      setComments([...comments, comment]);
      setNewComment('');
    } catch (err) {
      console.error('Failed to add comment:', err);
    } finally {
      setIsSubmittingComment(false);
    }
  };

  const handleDeleteComment = async (commentId) => {
    try {
      await deleteComment(commentId);
      setComments(comments.filter((c) => c.id !== commentId));
    } catch (err) {
      console.error('Failed to delete comment:', err);
    }
  };

  const handleUpvote = async () => {
    setIsUpvoting(true);
    try {
      const result = await toggleUpvote(solution.id);
      // Update local state
    } catch (err) {
      console.error('Failed to upvote:', err);
    } finally {
      setIsUpvoting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="bg-slate-900 border border-white/10 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {solution.user_avatar && (
              <img
                src={solution.user_avatar}
                alt={solution.user_username}
                className="w-10 h-10 rounded-full border border-white/20"
              />
            )}
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-white">
                {solution.is_anonymous ? 'Anonymous' : solution.user_username}
              </p>
              <p className="text-xs text-slate-400">{solution.quest_title}</p>
            </div>
            <span className={cn('px-2 py-1 rounded text-xs font-bold', langColor.bg, langColor.border, 'border', langColor.text)}>
              {solution.language.toUpperCase()}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 p-4">
            {/* Code Editor */}
            <div className="lg:col-span-2">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white">
                  {showDiff ? 'Diff View' : 'Solution Code'}
                </h3>
                <button
                  onClick={handleToggleDiff}
                  disabled={isLoadingDiff}
                  className="px-3 py-1 text-xs bg-primary/20 border border-primary/40 rounded text-primary hover:bg-primary/30 disabled:opacity-50 transition-colors"
                >
                  {isLoadingDiff ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    showDiff ? 'Hide Diff' : 'Show Diff'
                  )}
                </button>
              </div>

              {showDiff && diffData ? (
                <div className="bg-black/40 rounded border border-white/10 p-3 font-mono text-xs max-h-96 overflow-y-auto">
                  {diffData.diff_lines.map((line, idx) => (
                    <div
                      key={idx}
                      className={cn(
                        'py-0.5 px-2',
                        line.type === 'add' && 'bg-emerald-500/20 text-emerald-300',
                        line.type === 'remove' && 'bg-red-500/20 text-red-300',
                        line.type === 'same' && 'text-slate-400'
                      )}
                    >
                      {line.type === 'add' && '+ '}
                      {line.type === 'remove' && '- '}
                      {line.type === 'same' && '  '}
                      {line.text}
                    </div>
                  ))}
                </div>
              ) : (
                <Editor
                  height="400px"
                  language={solution.language}
                  value={solution.code}
                  options={{
                    readOnly: true,
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    fontSize: 12,
                  }}
                  theme="vs-dark"
                />
              )}
            </div>

            {/* Stats & Comments */}
            <div className="flex flex-col gap-4">
              {/* Stats */}
              <div className="bg-white/5 border border-white/10 rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Upvotes</span>
                  <span className="font-semibold text-white">{solution.upvote_count}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Views</span>
                  <span className="font-semibold text-white">{solution.views_count}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Solve Time</span>
                  <span className="font-semibold text-white">{solution.solve_time_minutes}m</span>
                </div>
                <button
                  onClick={handleUpvote}
                  disabled={isUpvoting}
                  className="w-full mt-3 px-3 py-2 bg-primary/20 border border-primary/40 rounded text-sm font-semibold text-primary hover:bg-primary/30 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                >
                  <ThumbsUp size={16} className={solution.user_upvoted ? 'fill-primary' : ''} />
                  {solution.user_upvoted ? 'Upvoted' : 'Upvote'}
                </button>
              </div>

              {/* Comments Preview */}
              <div className="text-xs text-slate-400">
                {comments.length} comment{comments.length !== 1 ? 's' : ''}
              </div>
            </div>
          </div>

          {/* Comments Section */}
          <div className="border-t border-white/10 p-4">
            <h3 className="text-sm font-semibold text-white mb-4">Comments</h3>

            {/* New Comment */}
            <div className="mb-6 flex gap-3">
              {user?.avatar_url && (
                <img
                  src={user.avatar_url}
                  alt={user.username}
                  className="w-8 h-8 rounded-full border border-white/20 flex-shrink-0"
                />
              )}
              <div className="flex-1">
                <textarea
                  placeholder="Share your thoughts..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  maxLength={1000}
                  rows={2}
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary/50 resize-none"
                />
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-slate-500">{newComment.length}/1000</span>
                  <button
                    onClick={handleAddComment}
                    disabled={isSubmittingComment || !newComment.trim()}
                    className="px-3 py-1 bg-primary/20 border border-primary/40 rounded text-xs font-semibold text-primary hover:bg-primary/30 disabled:opacity-50 transition-colors"
                  >
                    {isSubmittingComment ? <Loader2 size={14} className="animate-spin" /> : 'Comment'}
                  </button>
                </div>
              </div>
            </div>

            {/* Comments List */}
            <div className="space-y-4 max-h-64 overflow-y-auto">
              {comments.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-4">No comments yet. Be the first!</p>
              ) : (
                comments.map((comment) => (
                  <CommentThread
                    key={comment.id}
                    comment={comment}
                    onReply={(text, parentId) => addComment(solution.id, text, parentId)}
                    onDelete={handleDeleteComment}
                    currentUserId={user?.username}
                  />
                ))
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

export default function SolutionsPage() {
  const { questId } = useParams();
  const navigate = useNavigate();
  const [solutions, setSolutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sort, setSort] = useState('new');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedSolution, setSelectedSolution] = useState(null);
  const pageSize = 20;

  useEffect(() => {
    loadSolutions();
  }, [questId, sort, page]);

  const loadSolutions = async () => {
    try {
      setLoading(true);
      const data = await getSolutions({
        questId: questId ? parseInt(questId) : undefined,
        sort,
        page,
        pageSize,
      });
      setSolutions(data.results || []);
      setTotalCount(data.count || 0);
      setError(null);
    } catch (err) {
      setError(err.message);
      setSolutions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = async (solution) => {
    try {
      const detail = await getSolutionDetail(solution.id);
      setSelectedSolution(detail);
    } catch (err) {
      console.error('Failed to load solution detail:', err);
    }
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <MainLayout>
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Community Solutions</h1>
          <p className="text-slate-400">Learn from peer solutions and share your own</p>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between mb-6 gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-400">Sort by:</span>
            <select
              value={sort}
              onChange={(e) => {
                setSort(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white focus:outline-none focus:border-primary/50"
            >
              <option value="new">Newest</option>
              <option value="top">Most Upvoted</option>
              <option value="fastest">Fastest</option>
            </select>
          </div>
          <span className="text-sm text-slate-400">
            {totalCount} solution{totalCount !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Error */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3 text-red-400"
          >
            <AlertCircle size={20} />
            {error}
          </motion.div>
        )}

        {/* Loading */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={32} className="animate-spin text-primary" />
          </div>
        ) : solutions.length === 0 ? (
          <div className="text-center py-12">
            <Code2 size={48} className="mx-auto mb-4 text-slate-600" />
            <p className="text-slate-400">No solutions found</p>
          </div>
        ) : (
          <>
            {/* Solutions Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {solutions.map((solution) => (
                <SolutionCard
                  key={solution.id}
                  solution={solution}
                  onViewDetail={handleViewDetail}
                  isSelected={selectedSolution?.id === solution.id}
                />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white hover:bg-white/10 disabled:opacity-50 transition-colors"
                >
                  Previous
                </button>
                <span className="text-sm text-slate-400">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white hover:bg-white/10 disabled:opacity-50 transition-colors"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Solution Viewer Modal */}
      <AnimatePresence>
        {selectedSolution && (
          <SolutionViewer
            solution={selectedSolution}
            onClose={() => setSelectedSolution(null)}
          />
        )}
      </AnimatePresence>
    </div>
    </MainLayout>
  );
}
