import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  AlertCircle,
  CheckCircle,
  Cloud,
  Database,
  Edit,
  Plus,
  RefreshCw,
  Search,
  Settings,
  Trash2,
  Zap
} from 'lucide-react'
import toast from 'react-hot-toast'
import { integrationService, Integration, IntegrationStats } from '../services/integrationService'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import PageHeader from '../components/ui/PageHeader'

const IntegrationsPage: React.FC = () => {
  const { t, i18n } = useTranslation()
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [stats, setStats] = useState<IntegrationStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterHealth, setFilterHealth] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [selectedIntegrations, setSelectedIntegrations] = useState<string[]>([])
  const [syncingIntegrations, setSyncingIntegrations] = useState<Set<string>>(new Set())

  useEffect(() => {
    loadIntegrations()
    loadStats()
  }, [searchQuery, filterType, filterStatus, filterHealth, sortBy, sortOrder, page])

  const loadIntegrations = async () => {
    try {
      setLoading(true)
      const response = await integrationService.listIntegrations({
        query: searchQuery || undefined,
        type: filterType || undefined,
        is_active: filterStatus === 'active' ? true : filterStatus === 'inactive' ? false : undefined,
        health_status: filterHealth || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: 20
      })
      setIntegrations(response.integrations)
      setTotalPages(response.total_pages)
    } catch {
      toast.error(t('integrations.loadError'))
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const statsData = await integrationService.getIntegrationStats()
      setStats(statsData)
    } catch (error) {
      console.error('Failed to load integration stats:', error)
    }
  }

  const handleSyncIntegration = async (integrationId: string) => {
    try {
      setSyncingIntegrations((prev) => new Set(prev).add(integrationId))
      await integrationService.syncIntegration(integrationId)
      toast.success(t('integrations.syncSuccess'))
      loadIntegrations()
      loadStats()
    } catch {
      toast.error(t('integrations.syncError'))
    } finally {
      setSyncingIntegrations((prev) => {
        const newSet = new Set(prev)
        newSet.delete(integrationId)
        return newSet
      })
    }
  }

  const handleHealthCheck = async (integrationId: string) => {
    try {
      const healthData = await integrationService.healthCheck(integrationId)
      if (healthData.status === 'healthy') {
        toast.success(t('integrations.healthCheckSuccess'))
      } else {
        toast.error(t('integrations.healthCheckFailed', { message: healthData.message }))
      }
      loadIntegrations()
    } catch {
      toast.error(t('integrations.healthCheckError'))
    }
  }

  const handleDeleteIntegration = async (integrationId: string) => {
    if (!confirm(t('integrations.confirmDelete'))) return

    try {
      await integrationService.deleteIntegration(integrationId)
      toast.success(t('integrations.deleteSuccess'))
      loadIntegrations()
      loadStats()
    } catch {
      toast.error(t('integrations.deleteError'))
    }
  }

  const handleBulkOperation = async (operation: string) => {
    if (selectedIntegrations.length === 0) {
      toast.error(t('integrations.selectIntegrationsFirst'))
      return
    }

    try {
      await integrationService.bulkOperation(operation, selectedIntegrations)
      toast.success(t('integrations.bulkOperationSuccess'))
      setSelectedIntegrations([])
      loadIntegrations()
      loadStats()
    } catch {
      toast.error(t('integrations.bulkOperationError'))
    }
  }

  const toggleIntegrationSelection = (integrationId: string) => {
    setSelectedIntegrations((prev) =>
      prev.includes(integrationId) ? prev.filter((id) => id !== integrationId) : [...prev, integrationId]
    )
  }

  const selectAllIntegrations = () => {
    setSelectedIntegrations(integrations.map((integration) => integration.id))
  }

  const clearSelection = () => {
    setSelectedIntegrations([])
  }

  const getIntegrationIcon = (type?: string) => {
    const normalizedType = (type || '').toLowerCase()
    switch (normalizedType) {
      case 'sap':
      case 'oracle':
        return <Database size={16} />
      case 'api':
        return <Cloud size={16} />
      case 'webhook':
        return <Zap size={16} />
      default:
        return <Settings size={16} />
    }
  }

  const getHealthStatusTone = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-emerald-100 text-emerald-700'
      case 'warning':
        return 'bg-amber-100 text-amber-700'
      case 'error':
        return 'bg-red-100 text-red-700'
      default:
        return 'bg-slate-200 text-slate-700'
    }
  }

  return (
    <div>
      <PageHeader
        title={t('integrations.title')}
        subtitle={
          i18n.language === 'ar'
            ? 'إدارة التكاملات والمزامنة والصحة التشغيلية من مكان واحد.'
            : 'Manage integrations, sync operations, and health status in one place.'
        }
        action={
          <Link to="/integrations/new">
            <Button className="gap-2">
              <Plus size={16} />
              {t('integrations.createNew')}
            </Button>
          </Link>
        }
      />

      {stats && (
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Card className="card-hover">
            <p className="text-xs text-slate-500">{t('integrations.stats.total')}</p>
            <p className="mt-2 text-2xl font-bold text-slate-900">{stats.total_integrations}</p>
          </Card>
          <Card className="card-hover">
            <p className="text-xs text-slate-500">{t('integrations.stats.active')}</p>
            <p className="mt-2 text-2xl font-bold text-emerald-600">{stats.active_integrations}</p>
          </Card>
          <Card className="card-hover">
            <p className="text-xs text-slate-500">{t('integrations.stats.healthy')}</p>
            <p className="mt-2 text-2xl font-bold text-blue-600">{stats.healthy_integrations}</p>
          </Card>
          <Card className="card-hover">
            <p className="text-xs text-slate-500">{t('integrations.stats.errors')}</p>
            <p className="mt-2 text-2xl font-bold text-red-600">{stats.error_integrations}</p>
          </Card>
        </div>
      )}

      <Card className="mb-4">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
          <label className="relative xl:col-span-2">
            <Search className="pointer-events-none absolute end-3 top-3.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              className="input-field pe-9"
              placeholder={t('integrations.searchPlaceholder')}
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setPage(1)
              }}
            />
          </label>

          <select
            value={filterType}
            onChange={(e) => {
              setFilterType(e.target.value)
              setPage(1)
            }}
            className="input-field"
          >
            <option value="">{t('common.all')}</option>
            <option value="sap">{t('integrations.types.sap')}</option>
            <option value="oracle">{t('integrations.types.oracle')}</option>
            <option value="api">{t('integrations.types.api')}</option>
            <option value="webhook">{t('integrations.types.webhook')}</option>
          </select>

          <select
            value={filterStatus}
            onChange={(e) => {
              setFilterStatus(e.target.value)
              setPage(1)
            }}
            className="input-field"
          >
            <option value="">{t('common.all')}</option>
            <option value="active">{t('common.active')}</option>
            <option value="inactive">{t('common.inactive')}</option>
          </select>

          <select
            value={filterHealth}
            onChange={(e) => {
              setFilterHealth(e.target.value)
              setPage(1)
            }}
            className="input-field"
          >
            <option value="">{t('common.all')}</option>
            <option value="healthy">{t('integrations.health.healthy')}</option>
            <option value="warning">{t('integrations.health.warning')}</option>
            <option value="error">{t('integrations.health.error')}</option>
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

      {selectedIntegrations.length > 0 && (
        <Card className="mb-4 border-blue-200 bg-blue-50/80">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium text-blue-700">
              {t('integrations.selectedCount', { count: selectedIntegrations.length })}
            </p>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="secondary" onClick={() => handleBulkOperation('activate')}>
                {t('integrations.bulkActivate')}
              </Button>
              <Button size="sm" variant="secondary" onClick={() => handleBulkOperation('deactivate')}>
                {t('integrations.bulkDeactivate')}
              </Button>
              <Button size="sm" variant="secondary" onClick={() => handleBulkOperation('sync')}>
                {t('integrations.bulkSync')}
              </Button>
              <Button size="sm" variant="danger" onClick={() => handleBulkOperation('delete')}>
                {t('integrations.bulkDelete')}
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
      ) : integrations.length === 0 ? (
        <Card className="text-center">
          <Settings className="mx-auto mb-2 h-10 w-10 text-slate-300" />
          <h3 className="text-base font-semibold text-slate-900">{t('integrations.noIntegrations')}</h3>
          <p className="mt-1 text-sm text-slate-600">{t('integrations.noIntegrationsDescription')}</p>
        </Card>
      ) : (
        <div className="saas-table-wrap">
          <table className="saas-table">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    checked={selectedIntegrations.length > 0 && selectedIntegrations.length === integrations.length}
                    onChange={() =>
                      selectedIntegrations.length === integrations.length ? clearSelection() : selectAllIntegrations()
                    }
                  />
                </th>
                <th>{t('integrations.name')}</th>
                <th>{t('integrations.type')}</th>
                <th>{t('integrations.status')}</th>
                <th>{t('integrations.lastSync')}</th>
                <th>{t('common.actions', { defaultValue: i18n.language === 'ar' ? 'الإجراءات' : 'Actions' })}</th>
              </tr>
            </thead>
            <tbody>
              {integrations.map((integration) => {
                const integrationTypeKey = integration.type || integration.integration_type || 'custom'
                return (
                  <tr key={integration.id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedIntegrations.includes(integration.id)}
                        onChange={() => toggleIntegrationSelection(integration.id)}
                      />
                    </td>
                    <td>
                      <p className="font-semibold text-slate-900">{integration.name}</p>
                      {integration.description && <p className="mt-1 max-w-sm truncate text-xs text-slate-500">{integration.description}</p>}
                    </td>
                    <td>
                      <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
                        {getIntegrationIcon(integrationTypeKey)}
                        {t(`integrations.types.${integrationTypeKey}`)}
                      </span>
                    </td>
                    <td>
                      <div className="flex gap-2">
                        <span className={`rounded-full px-2 py-1 text-xs font-semibold ${integration.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-700'}`}>
                          {integration.is_active ? t('common.active') : t('common.inactive')}
                        </span>
                        <span className={`rounded-full px-2 py-1 text-xs font-semibold ${getHealthStatusTone(integration.health_status)}`}>
                          {t(`integrations.health.${integration.health_status}`)}
                        </span>
                      </div>
                    </td>
                    <td>
                      {integration.last_sync_at ? new Date(integration.last_sync_at).toLocaleDateString() : i18n.language === 'ar' ? 'لم تتم بعد' : 'Not yet'}
                    </td>
                    <td>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleSyncIntegration(integration.id)}
                          disabled={syncingIntegrations.has(integration.id)}
                          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 disabled:opacity-50"
                          title={t('integrations.sync')}
                        >
                          <RefreshCw size={16} className={syncingIntegrations.has(integration.id) ? 'animate-spin' : ''} />
                        </button>
                        <button
                          onClick={() => handleHealthCheck(integration.id)}
                          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
                          title={t('integrations.healthCheck')}
                        >
                          <CheckCircle size={16} />
                        </button>
                        <Link
                          to={`/integrations/${integration.id}/edit`}
                          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
                          title={t('integrations.edit')}
                        >
                          <Edit size={16} />
                        </Link>
                        <button
                          onClick={() => handleDeleteIntegration(integration.id)}
                          className="rounded-lg p-2 text-slate-500 hover:bg-red-50 hover:text-red-600"
                          title={t('integrations.delete')}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
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

export default IntegrationsPage
