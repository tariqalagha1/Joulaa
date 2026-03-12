import React, { useState, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { DndProvider, useDrag, useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Bot, Plus, Settings, Play, Save, Download, Upload,
  MessageSquare, Brain, Zap, Database, Globe, Code,
  ArrowRight, Trash2, Copy, Eye, ChevronDown, ChevronRight, Clock
} from 'lucide-react'
import toast from 'react-hot-toast'

// Types for the visual builder
interface AgentNode {
  id: string
  type: 'trigger' | 'action' | 'condition' | 'response'
  position: { x: number; y: number }
  data: {
    label: string
    description?: string
    config?: Record<string, any>
  }
  connections: string[]
}

interface AgentFlow {
  id: string
  name: string
  description: string
  nodes: AgentNode[]
  metadata: {
    created_at: string
    updated_at: string
    version: string
  }
}

// Node types available in the palette
const NODE_TYPES = {
  triggers: [
    { type: 'user_message', label: 'User Message', icon: MessageSquare, description: 'Triggered when user sends a message' },
    { type: 'webhook', label: 'Webhook', icon: Globe, description: 'Triggered by external webhook' },
    { type: 'schedule', label: 'Schedule', icon: Clock, description: 'Triggered on schedule' },
  ],
  actions: [
    { type: 'llm_call', label: 'LLM Call', icon: Brain, description: 'Call OpenAI/Claude API' },
    { type: 'api_request', label: 'API Request', icon: Database, description: 'Make HTTP API request' },
    { type: 'data_transform', label: 'Transform Data', icon: Code, description: 'Transform or process data' },
  ],
  conditions: [
    { type: 'if_condition', label: 'If Condition', icon: Zap, description: 'Conditional logic branch' },
    { type: 'switch', label: 'Switch', icon: Settings, description: 'Multiple condition branches' },
  ],
  responses: [
    { type: 'text_response', label: 'Text Response', icon: MessageSquare, description: 'Send text message' },
    { type: 'rich_response', label: 'Rich Response', icon: Bot, description: 'Send rich content' },
  ]
}

// Draggable node component
const DraggableNode: React.FC<{
  nodeType: any
  category: string
}> = ({ nodeType, category }) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'node',
    item: { nodeType, category },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  })

  const Icon = nodeType.icon

  return (
    <div
      ref={drag}
      className={`p-3 bg-white border border-gray-200 rounded-lg cursor-move hover:shadow-md transition-shadow ${
        isDragging ? 'opacity-50' : ''
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        <Icon size={16} className="text-primary-600" />
        <span className="text-sm font-medium text-gray-900">{nodeType.label}</span>
      </div>
      <p className="text-xs text-gray-600">{nodeType.description}</p>
    </div>
  )
}

// Canvas node component
const CanvasNode: React.FC<{
  node: AgentNode
  isSelected: boolean
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onUpdate: (id: string, data: Partial<AgentNode>) => void
}> = ({ node, isSelected, onSelect, onDelete, onUpdate }) => {
  const { t } = useTranslation()
  const [isEditing, setIsEditing] = useState(false)

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'trigger': return 'bg-green-100 border-green-300 text-green-800'
      case 'action': return 'bg-blue-100 border-blue-300 text-blue-800'
      case 'condition': return 'bg-yellow-100 border-yellow-300 text-yellow-800'
      case 'response': return 'bg-purple-100 border-purple-300 text-purple-800'
      default: return 'bg-gray-100 border-gray-300 text-gray-800'
    }
  }

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={`absolute p-4 rounded-lg border-2 cursor-pointer min-w-[200px] ${
        getNodeColor(node.type)
      } ${
        isSelected ? 'ring-2 ring-primary-500' : ''
      }`}
      style={{
        left: node.position.x,
        top: node.position.y,
      }}
      onClick={() => onSelect(node.id)}
      whileHover={{ scale: 1.02 }}
    >
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-medium">{node.data.label}</h4>
        <div className="flex items-center gap-1">
          <button
            onClick={(e) => {
              e.stopPropagation()
              setIsEditing(true)
            }}
            className="p-1 hover:bg-white/50 rounded"
          >
            <Settings size={14} />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDelete(node.id)
            }}
            className="p-1 hover:bg-red-100 rounded text-red-600"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
      {node.data.description && (
        <p className="text-sm opacity-80">{node.data.description}</p>
      )}
      
      {/* Connection points */}
      <div className="absolute -right-2 top-1/2 w-4 h-4 bg-white border-2 border-current rounded-full transform -translate-y-1/2" />
      <div className="absolute -left-2 top-1/2 w-4 h-4 bg-white border-2 border-current rounded-full transform -translate-y-1/2" />
    </motion.div>
  )
}

// Main Agent Studio component
const AgentStudio: React.FC = () => {
  const { t } = useTranslation()
  const canvasRef = useRef<HTMLDivElement | null>(null)
  const [flow, setFlow] = useState<AgentFlow>({
    id: 'new-flow',
    name: 'New Agent Flow',
    description: 'Drag and drop to build your agent',
    nodes: [],
    metadata: {
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      version: '1.0.0'
    }
  })
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [isPreviewMode, setIsPreviewMode] = useState(false)
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({
    triggers: true,
    actions: true,
    conditions: false,
    responses: true
  })

  // Drop handler for canvas
  const [{ isOver }, drop] = useDrop({
    accept: 'node',
    drop: (item: { nodeType: any; category: string }, monitor) => {
      const offset = monitor.getDropResult()
      const canvasRect = canvasRef.current?.getBoundingClientRect()
      if (!canvasRect) return

      const clientOffset = monitor.getClientOffset()
      if (!clientOffset) return

      const x = clientOffset.x - canvasRect.left
      const y = clientOffset.y - canvasRect.top

      addNode(item.nodeType, item.category, { x, y })
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
    }),
  })

  const addNode = (nodeType: any, category: string, position: { x: number; y: number }) => {
    const newNode: AgentNode = {
      id: `node-${Date.now()}`,
      type: category.slice(0, -1) as any, // Remove 's' from category
      position,
      data: {
        label: nodeType.label,
        description: nodeType.description,
        config: {}
      },
      connections: []
    }

    setFlow(prev => ({
      ...prev,
      nodes: [...prev.nodes, newNode],
      metadata: {
        ...prev.metadata,
        updated_at: new Date().toISOString()
      }
    }))

    toast.success(`Added ${nodeType.label} to canvas`)
  }

  const deleteNode = (nodeId: string) => {
    setFlow(prev => ({
      ...prev,
      nodes: prev.nodes.filter(node => node.id !== nodeId),
      metadata: {
        ...prev.metadata,
        updated_at: new Date().toISOString()
      }
    }))
    setSelectedNodeId(null)
    toast.success('Node deleted')
  }

  const updateNode = (nodeId: string, updates: Partial<AgentNode>) => {
    setFlow(prev => ({
      ...prev,
      nodes: prev.nodes.map(node => 
        node.id === nodeId ? { ...node, ...updates } : node
      ),
      metadata: {
        ...prev.metadata,
        updated_at: new Date().toISOString()
      }
    }))
  }

  const saveFlow = () => {
    // TODO: Implement save to backend
    const flowData = JSON.stringify(flow, null, 2)
    console.log('Saving flow:', flowData)
    toast.success('Agent flow saved successfully')
  }

  const testFlow = () => {
    // TODO: Implement flow testing
    toast.success('Testing agent flow...')
  }

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }))
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="h-screen flex bg-gray-50">
        {/* Sidebar - Node Palette */}
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              {t('agentStudio.title')}
            </h2>
            <p className="text-sm text-gray-600">
              {t('agentStudio.subtitle')}
            </p>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {Object.entries(NODE_TYPES).map(([category, nodes]) => (
              <div key={category} className="mb-6">
                <button
                  onClick={() => toggleCategory(category)}
                  className="flex items-center gap-2 w-full text-left mb-3 text-sm font-medium text-gray-700 hover:text-gray-900"
                >
                  {expandedCategories[category] ? (
                    <ChevronDown size={16} />
                  ) : (
                    <ChevronRight size={16} />
                  )}
                  {t(`agentStudio.categories.${category}`)}
                </button>
                
                <AnimatePresence>
                  {expandedCategories[category] && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="space-y-2"
                    >
                      {nodes.map((nodeType) => (
                        <DraggableNode
                          key={nodeType.type}
                          nodeType={nodeType}
                          category={category}
                        />
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </div>

        {/* Main Canvas Area */}
        <div className="flex-1 flex flex-col">
          {/* Toolbar */}
          <div className="bg-white border-b border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <input
                  type="text"
                  value={flow.name}
                  onChange={(e) => setFlow(prev => ({ ...prev, name: e.target.value }))}
                  className="text-lg font-semibold bg-transparent border-none focus:outline-none focus:ring-2 focus:ring-primary-500 rounded px-2"
                />
                <span className="text-sm text-gray-500">
                  {flow.nodes.length} {t('agentStudio.nodes')}
                </span>
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsPreviewMode(!isPreviewMode)}
                  className={`btn-secondary flex items-center gap-2 ${
                    isPreviewMode ? 'bg-primary-100 text-primary-700' : ''
                  }`}
                >
                  <Eye size={16} />
                  {t('agentStudio.preview')}
                </button>
                
                <button
                  onClick={testFlow}
                  className="btn-secondary flex items-center gap-2"
                >
                  <Play size={16} />
                  {t('agentStudio.test')}
                </button>
                
                <button
                  onClick={saveFlow}
                  className="btn-primary flex items-center gap-2"
                >
                  <Save size={16} />
                  {t('agentStudio.save')}
                </button>
              </div>
            </div>
          </div>

          {/* Canvas */}
          <div
            ref={(node) => {
              canvasRef.current = node
              drop(node)
            }}
            className={`flex-1 relative overflow-hidden ${
              isOver ? 'bg-primary-50' : 'bg-gray-100'
            }`}
            style={{
              backgroundImage: 'radial-gradient(circle, #e5e7eb 1px, transparent 1px)',
              backgroundSize: '20px 20px'
            }}
          >
            {flow.nodes.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <Bot size={48} className="text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    {t('agentStudio.emptyCanvas.title')}
                  </h3>
                  <p className="text-gray-600 max-w-md">
                    {t('agentStudio.emptyCanvas.description')}
                  </p>
                </div>
              </div>
            )}

            {/* Render nodes */}
            {flow.nodes.map((node) => (
              <CanvasNode
                key={node.id}
                node={node}
                isSelected={selectedNodeId === node.id}
                onSelect={setSelectedNodeId}
                onDelete={deleteNode}
                onUpdate={updateNode}
              />
            ))}

            {/* Drop overlay */}
            {isOver && (
              <div className="absolute inset-0 bg-primary-100/50 border-2 border-dashed border-primary-300 flex items-center justify-center">
                <div className="text-center">
                  <Plus size={48} className="text-primary-600 mx-auto mb-2" />
                  <p className="text-primary-700 font-medium">
                    {t('agentStudio.dropHere')}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Properties Panel */}
        {selectedNodeId && (
          <div className="w-80 bg-white border-l border-gray-200 p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {t('agentStudio.properties')}
            </h3>
            
            {/* Node properties form would go here */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('agentStudio.nodeName')}
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  value={flow.nodes.find(n => n.id === selectedNodeId)?.data.label || ''}
                  onChange={(e) => {
                    const node = flow.nodes.find(n => n.id === selectedNodeId)
                    if (node) {
                      updateNode(selectedNodeId, {
                        data: { ...node.data, label: e.target.value }
                      })
                    }
                  }}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('agentStudio.nodeDescription')}
                </label>
                <textarea
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  rows={3}
                  value={flow.nodes.find(n => n.id === selectedNodeId)?.data.description || ''}
                  onChange={(e) => {
                    const node = flow.nodes.find(n => n.id === selectedNodeId)
                    if (node) {
                      updateNode(selectedNodeId, {
                        data: { ...node.data, description: e.target.value }
                      })
                    }
                  }}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </DndProvider>
  )
}

export default AgentStudio
