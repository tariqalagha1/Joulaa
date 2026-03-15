import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { BarChart3, Copy, Edit, Play, Plus, Search, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { agentService, Agent, AgentStats } from '../services/agentService'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import PageHeader from '../components/ui/PageHeader'

const AgentsPage: React.FC = () => {
  const { t, i18n } = useTranslation()
  const [agents, setAgents] = useState<Agent[]>([])
  const [stats, setStats] = useState<AgentStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined)
  const [filterPublic, setFilterPublic] = useState<boolean | undefined>(undefined)
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [selectedAgents, setSelectedAgents] = useState<string[]>([])

  useEffect(() => {
    loadAgents()
    loadStats()
  }, [searchQuery, filterActive, filterPublic, sortBy, sortOrder, page])

  const loadAgents = async () => {
    try {
      setLoading(true)
      const response = await agentService.listAgents({
        query: searchQuery || undefined,
        is_active: filterActive,
        is_public: filterPublic,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: 20
      })
      setAgents(response.agents)
      setTotalPages(response.total_pages)
    } catch {
      toast.error(t('agents.loadError'))
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const statsData = await agentService.getAgentStats()
      setStats(statsData)
    } catch (error) {
      console.error('Failed to load agent stats:', error)
    }
  }

  const handleDeleteAgent = async (agentId: string) => {
    if (!confirm(t('agents.confirmDelete'))) return

    try {
      await agentService.deleteAgent(agentId)
      toast.success(t('agents.deleteSuccess'))
      loadAgents()
      loadStats()
    } catch {
      toast.error(t('agents.deleteError'))
    }
  }

  const handleCloneAgent = async (agentId: string, currentName: string) => {
    const newName = prompt(t('agents.clonePrompt'), `${currentName} (Copy)`)
    if (!newName) return

    try {
      await agentService.cloneAgent(agentId, newName)
      toast.success(t('agents.cloneSuccess'))
      loadAgents()
      loadStats()
    } catch {
      toast.error(t('agents.cloneError'))
    }
  }

  const handleBulkOperation = async (operation: string) => {
    if (selectedAgents.length === 0) {
      toast.error(t('agents.selectAgentsFirst'))
      return
    }

    try {
      await agentService.bulkOperation(operation, selectedAgents)
      toast.success(t('agents.bulkOperationSuccess'))
      setSelectedAgents([])
      loadAgents()
      loadStats()
    } catch {
      toast.error(t('agents.bulkOperationError'))
    }
  }

  const toggleAgentSelection = (agentId: string) => {
    setSelectedAgents((prev) => (prev.includes(agentId) ? prev.filter((id) => id !== agentId) : [...prev, agentId]))
  }

  const selectAllAgents = () => {
    setSelectedAgents(agents.map((agent) => agent.id))
  }

  const clearSelection = () => {
    setSelectedAgents([])
  }

  return (
    <div>
      <PageHeader
        title={t('agents.title')}
        subtitle={i18n.language === 'ar' ? 'إدارة دورة حياة الوكلاء من شاشة واحدة.' : 'Manage your agent lifecycle in one screen.'}
        action={
          <Link to="/dashboard/agent-studio">
            <Button className="gap-2">
              <Plus size={16} />
              {t('agents.createNew')}
            </Button>
          </Link>
        }
      />

      {stats && (
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Card className="card-hover">
            <p className="text-xs text-slate-500">{t('agents.stats.total')}</p>
            <p className="mt-2 text-2xl font-bold text-slate-900">{stats.total_agents}</p>
          </Card>
          <Card className="card-hover">
            <p className="text-xs text-slate-500">{t('agents.stats.active')}</p>
            <p className="mt-2 text-2xl font-bold text-emerald-600">{stats.active_agents}</p>
          </Card>
          <Card className="card-hover">
            <p className="text-xs text-slate-500">{t('agents.stats.conversations')}</p>
            <p className="mt-2 text-2xl font-bold text-blue-600">{stats.total_conversations}</p>
          </Card>
          <Card className="card-hover">
            <p className="text-xs text-slate-500">{t('agents.stats.avgConversations')}</p>
            <p className="mt-2 text-2xl font-bold text-slate-900">{stats.avg_conversations_per_agent.toFixed(1)}</p>
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
              placeholder={t('agents.searchPlaceholder')}
            />
          </label>

          <select
            value={filterActive === undefined ? '' : filterActive.toString()}
            onChange={(e) => {
              setFilterActive(e.target.value === '' ? undefined : e.target.value === 'true')
              setPage(1)
            }}
            className="input-field"
          >
            <option value="">{t('common.all')}</option>
            <option value="true">{t('common.active')}</option>
            <option value="false">{t('common.inactive')}</option>
          </select>

          <select
            value={filterPublic === undefined ? '' : filterPublic.toString()}
            onChange={(e) => {
              setFilterPublic(e.target.value === '' ? undefined : e.target.value === 'true')
              setPage(1)
            }}
            className="input-field"
          >
            <option value="">{t('common.all')}</option>
            <option value="true">{t('agents.public')}</option>
            <option value="false">{t('agents.private')}</option>
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
            <option value="created_at-desc">{t('common.newest')}</option>
            <option value="created_at-asc">{t('common.oldest')}</option>
            <option value="name-asc">{t('common.nameAZ')}</option>
            <option value="name-desc">{t('common.nameZA')}</option>
            <option value="updated_at-desc">{t('common.recentlyUpdated')}</option>
          </select>
        </div>
      </Card>

      {selectedAgents.length > 0 && (
        <Card className="mb-4 border-blue-200 bg-blue-50/80">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium text-blue-700">{t('agents.selectedCount', { count: selectedAgents.length })}</p>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="secondary" onClick={() => handleBulkOperation('activate')}>
                {t('agents.bulkActivate')}
              </Button>
              <Button size="sm" variant="secondary" onClick={() => handleBulkOperation('deactivate')}>
                {t('agents.bulkDeactivate')}
              </Button>
              <Button size="sm" variant="danger" onClick={() => handleBulkOperation('delete')}>
                {t('agents.bulkDelete')}
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
      ) : agents.length === 0 ? (
        <Card className="text-center">
          <BarChart3 className="mx-auto mb-2 h-10 w-10 text-slate-300" />
          <h3 className="text-base font-semibold text-slate-900">{t('agents.noAgents')}</h3>
          <p className="mt-1 text-sm text-slate-600">{t('agents.noAgentsDescription')}</p>
        </Card>
      ) : (
        <div className="saas-table-wrap">
          <table className="saas-table">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    checked={selectedAgents.length > 0 && selectedAgents.length === agents.length}
                    onChange={() => (selectedAgents.length === agents.length ? clearSelection() : selectAllAgents())}
                  />
                </th>
                <th>{t('agents.name')}</th>
                <th>{t('agents.status')}</th>
                <th>{t('agents.model')}</th>
                <th>{t('agents.createdAt')}</th>
                <th>{t('common.actions', { defaultValue: i18n.language === 'ar' ? 'الإجراءات' : 'Actions' })}</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((agent) => (
                <tr key={agent.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedAgents.includes(agent.id)}
                      onChange={() => toggleAgentSelection(agent.id)}
                    />
                  </td>
                  <td>
                    <p className="font-semibold text-slate-900">{agent.name}</p>
                    {agent.description && <p className="mt-1 max-w-md truncate text-xs text-slate-500">{agent.description}</p>}
                  </td>
                  <td>
                    <div className="flex gap-2">
                      <span className={`rounded-full px-2 py-1 text-xs font-semibold ${agent.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-700'}`}>
                        {agent.is_active ? t('common.active') : t('common.inactive')}
                      </span>
                      {agent.is_public && <span className="rounded-full bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-700">{t('agents.public')}</span>}
                    </div>
                  </td>
                  <td>{agent.model || 'Default'}</td>
                  <td>{new Date(agent.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className="flex items-center gap-1">
                      <Link to={`/agents/${agent.id}/test`} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700" title={t('agents.test')}>
                        <Play size={16} />
                      </Link>
                      <Link to={`/agents/${agent.id}/edit`} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700" title={t('agents.edit')}>
                        <Edit size={16} />
                      </Link>
                      <button onClick={() => handleCloneAgent(agent.id, agent.name)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700" title={t('agents.clone')}>
                        <Copy size={16} />
                      </button>
                      <button onClick={() => handleDeleteAgent(agent.id)} className="rounded-lg p-2 text-slate-500 hover:bg-red-50 hover:text-red-600" title={t('agents.delete')}>
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

export default AgentsPage
