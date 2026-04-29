/**
 * SkillTree AI - Skill Tree Page
 * Interactive skill tree visualization with React Flow
 * Displays depth hierarchy and manages skill progression
 * @module pages/SkillTreePage
 */

import { useEffect, useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import { Sparkles, Filter, Loader2, AlertCircle, Wand2, Layers } from 'lucide-react';
import { SKILL_STATUS } from '../constants';
import api from '../api/api';
import { cn } from '../utils/cn';
import SkillNode from '../components/skill-tree/SkillNode';
import SkillDetailPanel from '../components/skill-tree/SkillDetailPanel';
import TreeGeneratorPanel from '../components/skill-tree/TreeGeneratorPanel';
import MainLayout from '../components/layout/MainLayout';

/**
 * Category filter options
 */
const CATEGORIES = [
  { id: 'all', label: 'All', color: 'primary' },
  { id: 'algorithms', label: 'Algorithms', color: 'purple' },
  { id: 'data-structures', label: 'Data Structures', color: 'cyan' },
  { id: 'systems', label: 'Systems', color: 'amber' },
  { id: 'web-dev', label: 'Web Dev', color: 'pink' },
  { id: 'ai-ml', label: 'AI/ML', color: 'emerald' },
];

/**
 * Custom node types for React Flow
 */
const nodeTypes = {
  skillNode: SkillNode,
};

/**
 * Apply dagre layout to nodes
 */
const getLayoutedElements = (nodes, edges, direction = 'LR') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction, nodesep: 120, ranksep: 60 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 180, height: 100 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 90,
        y: nodeWithPosition.y - 50,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

/**
 * Skill Tree Page Component
 */
function SkillTreePage() {
  const navigate = useNavigate();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [activeCategory, setActiveCategory] = useState('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rawSkills, setRawSkills] = useState([]);
  const [showGenerator, setShowGenerator] = useState(false);
  const [treeDepth, setTreeDepth] = useState(0);  // NEW: Track tree depth

  /**
   * Fetch skill tree data from API
   */
  const fetchSkillTree = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.get('/api/skills/tree/');

      const data = response.data;

      if (!data || !data.nodes || !Array.isArray(data.nodes)) {
        throw new Error('Invalid API response structure');
      }

      setRawSkills(data.nodes);
      
      // NEW: Extract tree depth from response
      if (data.depth) {
        setTreeDepth(data.depth);
      }

      // Transform API data to React Flow format
      const flowNodes = data.nodes.map((skill) => ({
        id: String(skill.id),
        type: 'skillNode',
        data: {
          ...skill,
          tree_depth: skill.tree_depth || 0,  // NEW: Include depth in node data
          onClick: (skillData) => setSelectedSkill(skillData),
        },
        position: { x: 0, y: 0 },
      }));

      const flowEdges = (data.edges || []).map((edge, index) => ({
        id: `edge-${edge.source}-${edge.target}-${index}`,
        source: String(edge.source),
        target: String(edge.target),
        type: 'smoothstep',
        animated: false,
        style: {
          stroke: 'rgba(99, 102, 241, 0.3)',
          strokeWidth: 2,
        },
      }));

      // Apply dagre layout
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        flowNodes,
        flowEdges
      );

      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    } catch (err) {
      console.error('Failed to fetch skill tree:', err);
      setError(err.response?.data?.message || err.message || 'Failed to load skill tree');
    } finally {
      setIsLoading(false);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    fetchSkillTree();
  }, [fetchSkillTree]);

  /**
   * Filter nodes by category
   */
  const filteredNodes = useMemo(() => {
    if (activeCategory === 'all') return nodes;
    return nodes.filter((node) => node.data.category === activeCategory);
  }, [nodes, activeCategory]);

  /**
   * Filter edges to only show connections between visible nodes
   */
  const filteredEdges = useMemo(() => {
    const visibleNodeIds = new Set(filteredNodes.map((n) => n.id));
    return edges.filter(
      (edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)
    );
  }, [edges, filteredNodes]);

  /**
   * Handle category filter change
   */
  const handleCategoryChange = useCallback((categoryId) => {
    setActiveCategory(categoryId);
  }, []);

  /**
   * Handle start skill action
   */
  const handleStartSkill = useCallback(async (skillId) => {
    try {
      await api.post(`/api/skills/${skillId}/start/`, {});

      // Refresh skill tree
      await fetchSkillTree();
      setSelectedSkill(null);
    } catch (err) {
      console.error('Failed to start skill:', err);
      alert(err.response?.data?.message || 'Failed to start skill');
    }
  }, [fetchSkillTree]);

  /**
   * Loading skeleton
   */
  if (isLoading) {
    return (
      <div className="relative w-full min-h-screen bg-background overflow-hidden flex items-center justify-center">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#0a0c10] via-[#0f0a1a] to-[#0a0c10]" />
        
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative z-10 glass-panel p-12 rounded-3xl text-center"
        >
          <Loader2 size={48} className="text-primary animate-spin mx-auto mb-4" />
          <h2 className="text-2xl font-black text-white mb-2">Loading Skill Tree</h2>
          <p className="text-slate-400 text-sm">Initializing neural pathways...</p>
        </motion.div>

        {/* Vignette */}
        <div className="fixed inset-0 pointer-events-none shadow-[inset_0_0_150px_rgba(0,0,0,0.9)] z-0" />
      </div>
    );
  }

  /**
   * Error state
   */
  if (error) {
    return (
      <div className="relative w-full min-h-screen bg-background overflow-hidden flex items-center justify-center p-6">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#0a0c10] via-[#0f0a1a] to-[#0a0c10]" />
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative z-10 glass-panel p-12 rounded-3xl text-center max-w-md"
        >
          <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-4">
            <AlertCircle size={32} className="text-accent" />
          </div>
          <h2 className="text-2xl font-black text-white mb-2">Connection Failed</h2>
          <p className="text-slate-400 text-sm mb-6">{error}</p>
          <button
            onClick={fetchSkillTree}
            className="auth-btn-primary"
          >
            Retry Connection
          </button>
        </motion.div>

        {/* Vignette */}
        <div className="fixed inset-0 pointer-events-none shadow-[inset_0_0_150px_rgba(0,0,0,0.9)] z-0" />
      </div>
    );
  }

  return (
    <MainLayout>
      <div className="relative w-full h-screen bg-background overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#0a0c10] via-[#0f0a1a] to-[#0a0c10]" />

      {/* Header */}
      <motion.div
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="absolute top-0 left-0 right-0 z-20 p-6"
      >
        <div className="glass-panel px-8 py-4 rounded-2xl border-white/5 shadow-2xl backdrop-blur-3xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-2 rounded-xl bg-gradient-to-br from-primary to-accent shadow-lg shadow-primary/20">
                <Sparkles size={24} className="text-white" fill="currentColor" />
              </div>
              <div>
                <h1 className="text-2xl font-black tracking-tight text-white">
                  Skill Tree
                </h1>
                <p className="text-xs text-slate-400 uppercase tracking-wider">
                  {treeDepth > 0 ? `Depth Level ${treeDepth}` : 'Neural Pathway Visualization'}
                </p>
              </div>
            </div>

            {/* Filter Toolbar */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowGenerator(g => !g)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-bold hover:bg-primary/20 transition-all duration-200 mr-2',
                  showGenerator
                    ? 'bg-primary/20 border-primary/50 text-primary shadow-[0_0_12px_rgba(99,102,241,0.3)]'
                    : 'bg-primary/10 border-primary/30 text-primary'
                )}
              >
                <Wand2 size={13} /> {showGenerator ? 'Close' : 'AI Builder'}
              </button>
              <Filter size={16} className="text-slate-500" />
              {CATEGORIES.map((category) => (
                <button
                  key={category.id}
                  onClick={() => handleCategoryChange(category.id)}
                  className={cn(
                    'px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-300 backdrop-blur-md border',
                    activeCategory === category.id
                      ? 'bg-primary/20 border-primary/50 text-primary shadow-[0_0_15px_rgba(99,102,241,0.3)]'
                      : 'bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white'
                  )}
                >
                  {category.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* React Flow Canvas */}
      <div className="absolute inset-0 z-10">
        <ReactFlow
          nodes={filteredNodes}
          edges={filteredEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.1}
          maxZoom={1.5}
          defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
          proOptions={{ hideAttribution: true }}
        >
          <Background
            color="rgba(99, 102, 241, 0.1)"
            gap={20}
            size={1}
            style={{ backgroundColor: 'transparent' }}
          />
          
          <Controls
            className="!bg-black/40 !backdrop-blur-xl !border !border-white/10 !rounded-xl !shadow-2xl"
            style={{
              button: {
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                color: 'rgba(255, 255, 255, 0.6)',
              },
            }}
          />
          
          <MiniMap
            className="!bg-black/40 !backdrop-blur-xl !border !border-white/10 !rounded-xl !shadow-2xl"
            nodeColor={(node) => {
              if (node.data.status === SKILL_STATUS.COMPLETED) return '#10b981';
              if (node.data.status === SKILL_STATUS.AVAILABLE) return '#6366f1';
              if (node.data.status === SKILL_STATUS.IN_PROGRESS) return '#06b6d4';
              return '#64748b';
            }}
            maskColor="rgba(0, 0, 0, 0.6)"
          />
        </ReactFlow>
      </div>

      {/* Skill Detail Panel */}
      <AnimatePresence>
        {selectedSkill && (
          <SkillDetailPanel
            skill={selectedSkill}
            onClose={() => setSelectedSkill(null)}
            onStartSkill={handleStartSkill}
          />
        )}
      </AnimatePresence>

      {/* Tree Generator Panel */}
      <AnimatePresence>
        {showGenerator && (
          <TreeGeneratorPanel
            onClose={() => setShowGenerator(false)}
            onTreeGenerated={() => {
              fetchSkillTree();
              setShowGenerator(false);
            }}
          />
        )}
      </AnimatePresence>

      {/* Vignette */}
      <div className="fixed inset-0 pointer-events-none shadow-[inset_0_0_150px_rgba(0,0,0,0.9)] z-0" />
    </div>
    </MainLayout>
  );
}

export default SkillTreePage;
