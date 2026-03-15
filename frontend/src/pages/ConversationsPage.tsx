import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Calendar, Download, Eye, MessageSquare, Plus, Search, Share2, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { conversationService, Conversation, ConversationStats } from '../services/conversationService'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import PageHeader from '../components/ui/PageHeader'

const ConversationsPage: React.FC = () => {
  const { t, i18n } = useTranslation()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [stats, setStats] = useState<ConversationStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterAgent, setFilterAgent] = useState('')
  const [filterDateRange, setFilterDateRange] = useState('')
  const [sortBy, setSortBy] = useState('updated_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [selectedConversations, setSelectedConversations] = useState<string[]>([])

  useEffect(() => {
    loadConversations()
    loadStats()
  }, [searchQuery, filterAgent, filterDateRange, sortBy, sortOrder, page])

  const loadConversations = async () => {
    try {
      setLoading(true)
      const response = await conversationService.listConversations({
        query: searchQuery || undefined,
        agent_id: filterAgent || undefined,
        date_from: filterDateRange === 'today' ? new Date().toISOString().split('T')[0] : undefined,
        date_to: filterDateRange === 'today' ? new Date().toISOString().split('T')[0] : undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: 20
      })
      setConversations(response.conversations)
      setTotalPages(response.total_pages)
    } catch {
      toast.error(t('conversations.loadError'))
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const statsData = await conversationService.getConversationStats()
      setStats(statsData)
    } catch (error) {
      console.error('Failed to load conversation stats:', error)
    }
  }

  const handleDeleteConversation = async (conversationId: string) => {
    if (!confirm(t('conversations.confirmDelete'))) return

    try {
      await conversationService.deleteConversation(conversationId)
      toast.success(t('conversations.deleteSuccess'))
      loadConversations()
      loadStats()
    } catch {
      toast.error(t('conversations.deleteError'))
    }
  }

  const handleShareConversation = async (conversationId: string) => {
    try {
      const shareData = await conversationService.shareConversation(conversationId, { is_public: true })
      navigator.clipboard.writeText(shareData.share_url)
      toast.success(t('conversations.shareSuccess'))
    } catch {
      toast.error(t('conversations.shareError'))
    }
  }

  const handleExportConversation = async (conversationId: string, format: 'json' | 'txt' | 'pdf') => {
    try {
      const blob = await conversationService.exportConversation(conversationId, format)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      a.download = `conversation-${conversationId}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      toast.success(t('conversations.exportSuccess'))
    } catch {
      toast.error(t('conversations.exportError'))
    }
  }

  const handleBulkOperation = async (operation: string) => {
    if (selectedConversations.length === 0) {
      toast.error(t('conversations.selectConversationsFirst'))
      return
    }

    try {
      await conversationService.bulkOperation(operation, selectedConversations)
      toast.success(t('conversations.bulkOperationSuccess'))
      setSelectedConversations([])
      loadConversations()
      loadStats()
    } catch {
      toast.error(t('conversations.bulkOperationError'))
    }
  }

  const toggleConversationSelection = (conversationId: string) => {
    setSelectedConversations((prev) =>
      prev.includes(conversationId) ? prev.filter((id) => id !== conversationId) : [...prev, conversationId]
    )
  }

  const selectAllConversations = () => {
    setSelectedConversations(conversations.map((conv) => conv.id))
  }

  const clearSelection = () => {
    setSelectedConversations([])
  }

  return (
    <div>
      <PageHeader
        title={t('conversations.title')}
        subtitle={
          i18n.language === 'ar' ? 'متابعة المحادثات، التفاعل، والتصدير من لوحة واحدة.' : 'Track, review, and export conversations from one view.'
        }
        action={
          <Link to="/dashboard/chat">
            <Button className="gap-2">
              <Plus size={16} />
              {t('conversations.startNew')}
            </Button>
          </Link>
        }
      />

      {stats && (
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Card className="card-hover">
            <p className="text-xs text-slate-500">{t('conversations.stats.total')}</p>
            <p className="mt-2 text-2xl font-bold text-slate-900">{stats.total_conversations}</p>
          </Card>
          <Card className="card-hover">
            <p className="text-xs text-slate-500">{t('conversations.stats.today')}</p>
            <p className="mt-2 text-2xl font-bold text-emerald-600">{stats.conversations_today}</p>
          </Card>
          <Card className="card-hover">
            <p className="text-xs text-slate-500">{t('conversations.stats.totalMessages')}</p>
            <p className="mt-2 text-2xl font-bold text-blue-600">{stats.total_messages}</p>
          </Card>
          <Card className="card-hover">
            <p className="text-xs text-slate-500">{t('conversations.stats.avgLength')}</p>
            <p className="mt-2 text-2xl font-bold text-slate-900">{stats.avg_messages_per_conversation.toFixed(1)}</p>
          </Card>
        </div>
      )}

      <Card className="mb-4">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
          <label className="relative xl:col-span-2">
            <Search className="pointer-events-none absolute end-3 top-3.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setPage(1)
              }}
              className="input-field pe-9"
              placeholder={t('conversations.searchPlaceholder')}
            />
          </label>

          <input
            type="text"
            value={filterAgent}
            onChange={(e) => {
              setFilterAgent(e.target.value)
              setPage(1)
            }}
            placeholder={t('conversations.filters.agentPlaceholder')}
            className="input-field"
          />

          <select
            value={filterDateRange}
            onChange={(e) => {
              setFilterDateRange(e.target.value)
              setPage(1)
            }}
            className="input-field"
          >
            <option value="">{t('common.all')}</option>
            <option value="today">{t('conversations.filters.today')}</option>
            <option value="week">{t('conversations.filters.thisWeek')}</option>
            <option value="month">{t('conversations.filters.thisMonth')}</option>
            <option value="year">{t('conversations.filters.thisYear')}</option>
          </select>

          <select
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split('-')
              setSortBy(field)
              setSortOrder(order as 'asc' | 'desc')
              setPage(1)
            }}
            className="input-field"
          >
            <option value="updated_at-desc">{t('conversations.sort.recentlyUpdated')}</option>
            <option value="created_at-desc">{t('conversations.sort.newest')}</option>
            <option value="created_at-asc">{t('conversations.sort.oldest')}</option>
            <option value="title-asc">{t('conversations.sort.titleAZ')}</option>
            <option value="title-desc">{t('conversations.sort.titleZA')}</option>
          </select>
        </div>
      </Card>

      {selectedConversations.length > 0 && (
        <Card className="mb-4 border-blue-200 bg-blue-50/80">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium text-blue-700">{t('conversations.selectedCount', { count: selectedConversations.length })}</p>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="secondary" onClick={() => handleBulkOperation('export')}>
                {t('conversations.bulkExport')}
              </Button>
              <Button size="sm" variant="danger" onClick={() => handleBulkOperation('delete')}>
                {t('conversations.bulkDelete')}
              </Button>
              <Button size="sm" variant="ghost" onClick={clearSelection}>
                {t('common.clearSelection')}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {loading ? (
        <Card>
          <div className="space-y-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="skeleton h-12 w-full" />
            ))}
          </div>
        </Card>
      ) : conversations.length === 0 ? (
        <Card className="text-center">
          <MessageSquare className="mx-auto mb-2 h-10 w-10 text-slate-300" />
          <h3 className="text-base font-semibold text-slate-900">{t('conversations.noConversations')}</h3>
          <p className="mt-1 text-sm text-slate-600">{t('conversations.noConversationsDescription')}</p>
        </Card>
      ) : (
        <div className="saas-table-wrap">
          <table className="saas-table">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    checked={selectedConversations.length > 0 && selectedConversations.length === conversations.length}
                    onChange={() =>
                      selectedConversations.length === conversations.length ? clearSelection() : selectAllConversations()
                    }
                  />
                </th>
                <th>{t('conversations.title')}</th>
                <th>{t('conversations.messages')}</th>
                <th>{t('conversations.participants')}</th>
                <th>{t('common.updatedAt', { defaultValue: i18n.language === 'ar' ? 'آخر تحديث' : 'Updated' })}</th>
                <th>{t('common.actions', { defaultValue: i18n.language === 'ar' ? 'الإجراءات' : 'Actions' })}</th>
              </tr>
            </thead>
            <tbody>
              {conversations.map((conversation) => (
                <tr key={conversation.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedConversations.includes(conversation.id)}
                      onChange={() => toggleConversationSelection(conversation.id)}
                    />
                  </td>
                  <td>
                    <Link to={`/dashboard/chat/${conversation.id}`} className="font-semibold text-slate-900 hover:text-blue-700">
                      {conversation.title || t('conversations.untitled')}
                    </Link>
                  </td>
                  <td>{conversation.message_count}</td>
                  <td>{conversation.agent_id || t('conversations.unknownAgent')}</td>
                  <td>
                    <div className="inline-flex items-center gap-1 text-slate-600">
                      <Calendar size={14} />
                      {new Date(conversation.updated_at || conversation.created_at).toLocaleDateString()}
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center gap-1">
                      <Link to={`/dashboard/chat/${conversation.id}`} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700" title={t('conversations.view')}>
                        <Eye size={16} />
                      </Link>
                      <button
                        onClick={() => handleShareConversation(conversation.id)}
                        className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
                        title={t('conversations.share')}
                      >
                        <Share2 size={16} />
                      </button>
                      <button
                        onClick={() => handleExportConversation(conversation.id, 'json')}
                        className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
                        title={t('conversations.export')}
                      >
                        <Download size={16} />
                      </button>
                      <button
                        onClick={() => handleDeleteConversation(conversation.id)}
                        className="rounded-lg p-2 text-slate-500 hover:bg-red-50 hover:text-red-600"
                        title={t('conversations.delete')}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="mt-5 flex items-center justify-between">
          <Button variant="secondary" onClick={() => setPage((prev) => prev - 1)} disabled={page === 1}>
            {t('common.previous')}
          </Button>
          <p className="text-sm text-slate-600">
            {i18n.language === 'ar' ? 'الصفحة' : 'Page'} {page} / {totalPages}
          </p>
          <Button variant="secondary" onClick={() => setPage((prev) => prev + 1)} disabled={page === totalPages}>
            {t('common.next')}
          </Button>
        </div>
      )}
    </div>
  )
}

export default ConversationsPage
