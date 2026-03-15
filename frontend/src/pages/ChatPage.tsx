import React, { Suspense, lazy, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Bot, MessageSquare, Settings } from 'lucide-react'
import { motion } from 'framer-motion'

import { conversationService } from '../services/conversationService'
import { agentService } from '../services/agentService'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'

const ConversationsList = lazy(() => import('../components/Chat/ConversationsList'))
const ChatInterface = lazy(() => import('../components/Chat/ChatInterface'))

const ChatPage: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { conversationId } = useParams<{ conversationId?: string }>()
  const [selectedConversationId, setSelectedConversationId] = useState<string | undefined>(conversationId)
  const [selectedAgentId, setSelectedAgentId] = useState<string | undefined>()
  const [showAgentSelector, setShowAgentSelector] = useState(false)

  const { data: conversation } = useQuery({
    queryKey: ['conversation', selectedConversationId],
    queryFn: () => conversationService.getConversation(selectedConversationId!),
    enabled: !!selectedConversationId
  })

  const { data: agentsData } = useQuery({
    queryKey: ['agents', 'active'],
    queryFn: () =>
      agentService.listAgents({
        is_active: true,
        page_size: 50
      })
  })

  useEffect(() => {
    if (conversationId && conversationId !== selectedConversationId) {
      setSelectedConversationId(conversationId)
    }
  }, [conversationId, selectedConversationId])

  useEffect(() => {
    if (conversation?.agent_id) {
      setSelectedAgentId(conversation.agent_id)
    }
  }, [conversation])

  const handleSelectConversation = (id: string) => {
    setSelectedConversationId(id)
    navigate(`/dashboard/chat/${id}`)
  }

  const handleNewConversation = () => {
    setSelectedConversationId(undefined)
    setSelectedAgentId(undefined)
    setShowAgentSelector(true)
    navigate('/dashboard/chat')
  }

  const handleAgentSelect = (agentId: string) => {
    setSelectedAgentId(agentId)
    setShowAgentSelector(false)
  }

  const agents = agentsData?.agents || []
  const selectedAgent = agents.find((agent) => agent.id === selectedAgentId)

  return (
    <div className="flex min-h-[calc(100vh-9rem)] overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-soft">
      <Suspense fallback={<div className="hidden w-80 border-e border-slate-200 bg-white md:block" />}>
        <ConversationsList
          selectedConversationId={selectedConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
        />
      </Suspense>

      <div className="flex flex-1 flex-col bg-slate-50/40">
        {selectedConversationId ? (
          <>
            <div className="border-b border-slate-200 bg-white/70 px-4 py-4 backdrop-blur-xl sm:px-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
                    <Bot size={18} />
                  </div>
                  <div>
                    <h1 className="text-base font-semibold text-slate-900 sm:text-lg">{conversation?.title || t('chat.conversation')}</h1>
                    {selectedAgent && <p className="text-xs text-slate-500 sm:text-sm">{t('chat.poweredBy')} {selectedAgent.name}</p>}
                  </div>
                </div>

                <button
                  onClick={() => setShowAgentSelector(true)}
                  className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
                  title={t('chat.changeAgent')}
                >
                  <Settings size={18} />
                </button>
              </div>
            </div>

            <Suspense
              fallback={
                <div className="p-4 sm:p-6">
                  <div className="skeleton h-10 w-full" />
                  <div className="skeleton mt-3 h-64 w-full" />
                </div>
              }
            >
              <ChatInterface conversationId={selectedConversationId} agentId={selectedAgentId} />
            </Suspense>
          </>
        ) : (
          <div className="flex flex-1 items-center justify-center p-4 sm:p-8">
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-2xl">
              <Card className="text-center">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-100 text-blue-600">
                  <MessageSquare size={26} />
                </div>

                <h2 className="text-2xl font-bold text-slate-900">{t('chat.welcome.title')}</h2>
                <p className="mx-auto mt-2 max-w-xl text-sm text-slate-600 sm:text-base">{t('chat.welcome.description')}</p>

                {showAgentSelector ? (
                  <div className="mt-6 space-y-3 text-start">
                    <h3 className="text-sm font-semibold text-slate-800">{t('chat.selectAgent')}</h3>
                    <div className="grid max-h-72 gap-2 overflow-y-auto">
                      {agents.map((agent) => (
                        <button
                          key={agent.id}
                          onClick={() => handleAgentSelect(agent.id)}
                          className="rounded-xl border border-slate-200 bg-white p-3 text-start transition hover:-translate-y-0.5 hover:border-blue-300 hover:bg-blue-50/60"
                        >
                          <p className="font-semibold text-slate-900">{agent.name}</p>
                          {agent.description && <p className="mt-1 line-clamp-2 text-xs text-slate-500">{agent.description}</p>}
                        </button>
                      ))}
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => setShowAgentSelector(false)}>
                      {t('common.cancel')}
                    </Button>
                  </div>
                ) : (
                  <div className="mt-6">
                    <Button onClick={() => setShowAgentSelector(true)}>{t('chat.startNewChat')}</Button>
                  </div>
                )}
              </Card>
            </motion.div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatPage
