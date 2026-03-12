import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Plus,
  Search,
  Filter,
  Settings,
  Play,
  Pause,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Clock,
  Database,
  Cloud,
  Zap,
  Edit,
  Trash2,
  MoreVertical
} from 'lucide-react'
import { integrationService, Integration, IntegrationStats } from '../services/integrationService'
import toast from 'react-hot-toast'

const IntegrationsPage: React.FC = () => {
  const { t } = useTranslation()
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
  const [showFilters, setShowFilters] = useState(false)
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
    } catch (error) {
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
      setSyncingIntegrations(prev => new Set(prev).add(integrationId))
      await integrationService.syncIntegration(integrationId)
      toast.success(t('integrations.syncSuccess'))
      loadIntegrations()
      loadStats()
    } catch (error) {
      toast.error(t('integrations.syncError'))
    } finally {
      setSyncingIntegrations(prev => {
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
    } catch (error) {
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
    } catch (error) {
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
    } catch (error) {
      toast.error(t('integrations.bulkOperationError'))
    }
  }

  const toggleIntegrationSelection = (integrationId: string) => {
    setSelectedIntegrations(prev => 
      prev.includes(integrationId) 
        ? prev.filter(id => id !== integrationId)
        : [...prev, integrationId]
    )
  }

  const selectAllIntegrations = () => {
    setSelectedIntegrations(integrations.map(integration => integration.id))
  }

  const clearSelection = () => {
    setSelectedIntegrations([])
  }

  const getIntegrationIcon = (type?: string) => {
    const normalizedType = (type || '').toLowerCase()
    switch (normalizedType) {
      case 'sap':
        return <Database className="h-6 w-6" />
      case 'oracle':
        return <Database className="h-6 w-6" />
      case 'api':
        return <Cloud className="h-6 w-6" />
      case 'webhook':
        return <Zap className="h-6 w-6" />
      default:
        return <Settings className="h-6 w-6" />
    }
  }

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-500'
      case 'warning':
        return 'text-yellow-500'
      case 'error':
        return 'text-red-500'
      default:
        return 'text-gray-500'
    }
  }

  const getHealthStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5" />
      case 'warning':
        return <AlertCircle className="h-5 w-5" />
      case 'error':
        return <AlertCircle className="h-5 w-5" />
      default:
        return <Clock className="h-5 w-5" />
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {t('integrations.title')}
                </h1>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  {t('integrations.subtitle')}
                </p>
              </div>
              <Link
                to="/integrations/new"
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Plus className="-ml-1 mr-2 h-5 w-5" />
                {t('integrations.createNew')}
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Settings className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                        {t('integrations.stats.total')}
                      </dt>
                      <dd className="text-lg font-medium text-gray-900 dark:text-white">
                        {stats.total_integrations}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <CheckCircle className="h-6 w-6 text-green-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                        {t('integrations.stats.active')}
                      </dt>
                      <dd className="text-lg font-medium text-gray-900 dark:text-white">
                        {stats.active_integrations}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <CheckCircle className="h-6 w-6 text-green-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                        {t('integrations.stats.healthy')}
                      </dt>
                      <dd className="text-lg font-medium text-gray-900 dark:text-white">
                        {stats.healthy_integrations}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <AlertCircle className="h-6 w-6 text-red-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                        {t('integrations.stats.errors')}
                      </dt>
                      <dd className="text-lg font-medium text-gray-900 dark:text-white">
                        {stats.error_integrations}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters and Search */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
          <div className="p-6">
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search */}
              <div className="flex-1">
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Search className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md leading-5 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    placeholder={t('integrations.searchPlaceholder')}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </div>

              {/* Filter Toggle */}
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Filter className="-ml-1 mr-2 h-5 w-5" />
                {t('common.filters')}
              </button>
            </div>

            {/* Expanded Filters */}
            {showFilters && (
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      {t('integrations.filters.type')}
                    </label>
                    <select
                      value={filterType}
                      onChange={(e) => setFilterType(e.target.value)}
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
                    >
                      <option value="">{t('common.all')}</option>
                      <option value="sap">{t('integrations.types.sap')}</option>
                      <option value="oracle">{t('integrations.types.oracle')}</option>
                      <option value="api">{t('integrations.types.api')}</option>
                      <option value="webhook">{t('integrations.types.webhook')}</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      {t('integrations.filters.status')}
                    </label>
                    <select
                      value={filterStatus}
                      onChange={(e) => setFilterStatus(e.target.value)}
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
                    >
                      <option value="">{t('common.all')}</option>
                      <option value="active">{t('common.active')}</option>
                      <option value="inactive">{t('common.inactive')}</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      {t('integrations.filters.health')}
                    </label>
                    <select
                      value={filterHealth}
                      onChange={(e) => setFilterHealth(e.target.value)}
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
                    >
                      <option value="">{t('common.all')}</option>
                      <option value="healthy">{t('integrations.health.healthy')}</option>
                      <option value="warning">{t('integrations.health.warning')}</option>
                      <option value="error">{t('integrations.health.error')}</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      {t('common.sortBy')}
                    </label>
                    <select
                      value={`${sortBy}-${sortOrder}`}
                      onChange={(e) => {
                        const [field, order] = e.target.value.split('-')
                        setSortBy(field)
                        setSortOrder(order as 'asc' | 'desc')
                      }}
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
                    >
                      <option value="created_at-desc">{t('common.newest')}</option>
                      <option value="created_at-asc">{t('common.oldest')}</option>
                      <option value="name-asc">{t('common.nameAZ')}</option>
                      <option value="name-desc">{t('common.nameZA')}</option>
                      <option value="updated_at-desc">{t('common.recentlyUpdated')}</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedIntegrations.length > 0 && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <span className="text-sm text-blue-700 dark:text-blue-300">
                  {t('integrations.selectedCount', { count: selectedIntegrations.length })}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleBulkOperation('activate')}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
                >
                  {t('integrations.bulkActivate')}
                </button>
                <button
                  onClick={() => handleBulkOperation('deactivate')}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
                >
                  {t('integrations.bulkDeactivate')}
                </button>
                <button
                  onClick={() => handleBulkOperation('sync')}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
                >
                  {t('integrations.bulkSync')}
                </button>
                <button
                  onClick={() => handleBulkOperation('delete')}
                  className="text-sm text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
                >
                  {t('integrations.bulkDelete')}
                </button>
                <button
                  onClick={clearSelection}
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                >
                  {t('common.clearSelection')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Integrations List */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 pb-12">
        {loading ? (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <div className="animate-pulse">
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
                      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : integrations.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 text-center">
            <div className="mx-auto h-12 w-12 text-gray-400">
              <Settings className="h-12 w-12" />
            </div>
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
              {t('integrations.noIntegrations')}
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {t('integrations.noIntegrationsDescription')}
            </p>
            <div className="mt-6">
              <Link
                to="/integrations/new"
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Plus className="-ml-1 mr-2 h-5 w-5" />
                {t('integrations.createFirst')}
              </Link>
            </div>
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 shadow overflow-hidden rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <input
                    type="checkbox"
                    checked={selectedIntegrations.length === integrations.length}
                    onChange={() => selectedIntegrations.length === integrations.length ? clearSelection() : selectAllIntegrations()}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {t('common.selectAll')}
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                {integrations.map((integration) => {
                  const integrationTypeKey = integration.type || integration.integration_type || 'custom'
                  return (
                    <div
                      key={integration.id}
                    className={`border border-gray-200 dark:border-gray-600 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors ${
                      selectedIntegrations.includes(integration.id) ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <input
                          type="checkbox"
                          checked={selectedIntegrations.includes(integration.id)}
                          onChange={() => toggleIntegrationSelection(integration.id)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <div className="flex-shrink-0 text-gray-400">
                          {getIntegrationIcon(integrationTypeKey)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                              {integration.name}
                            </h3>
                            <div className="flex items-center space-x-2">
                              {integration.is_active ? (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                                  {t('common.active')}
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400">
                                  {t('common.inactive')}
                                </span>
                              )}
                              <div className={`flex items-center space-x-1 ${getHealthStatusColor(integration.health_status)}`}>
                                {getHealthStatusIcon(integration.health_status)}
                                <span className="text-xs font-medium">
                                  {t(`integrations.health.${integration.health_status}`)}
                                </span>
                              </div>
                            </div>
                          </div>
                          {integration.description && (
                            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                              {integration.description}
                            </p>
                          )}
                          <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                            <span>{t('integrations.type')}: {t(`integrations.types.${integrationTypeKey}`)}</span>
                            <span>{t('integrations.createdAt')}: {new Date(integration.created_at).toLocaleDateString()}</span>
                            {integration.last_sync_at && (
                              <span>{t('integrations.lastSync')}: {new Date(integration.last_sync_at).toLocaleDateString()}</span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleSyncIntegration(integration.id)}
                          disabled={syncingIntegrations.has(integration.id)}
                          className="inline-flex items-center p-2 border border-transparent rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                          title={t('integrations.sync')}
                        >
                          <RefreshCw className={`h-5 w-5 ${syncingIntegrations.has(integration.id) ? 'animate-spin' : ''}`} />
                        </button>
                        <button
                          onClick={() => handleHealthCheck(integration.id)}
                          className="inline-flex items-center p-2 border border-transparent rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                          title={t('integrations.healthCheck')}
                        >
                          <CheckCircle className="h-5 w-5" />
                        </button>
                        <Link
                          to={`/integrations/${integration.id}/edit`}
                          className="inline-flex items-center p-2 border border-transparent rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                          title={t('integrations.edit')}
                        >
                          <Edit className="h-5 w-5" />
                        </Link>
                        <button
                          onClick={() => handleDeleteIntegration(integration.id)}
                          className="inline-flex items-center p-2 border border-transparent rounded-md text-gray-400 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                          title={t('integrations.delete')}
                        >
                          <Trash2 className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-6 flex items-center justify-between">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {t('common.previous')}
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page === totalPages}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {t('common.next')}
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {t('common.pagination.showing')} <span className="font-medium">{(page - 1) * 20 + 1}</span> {t('common.pagination.to')}{' '}
                  <span className="font-medium">{Math.min(page * 20, integrations.length)}</span> {t('common.pagination.of')}{' '}
                  <span className="font-medium">{integrations.length}</span> {t('common.pagination.results')}
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                  <button
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {t('common.previous')}
                  </button>
                  {[...Array(totalPages)].map((_, i) => (
                    <button
                      key={i + 1}
                      onClick={() => setPage(i + 1)}
                      className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                        page === i + 1
                          ? 'z-10 bg-blue-50 dark:bg-blue-900/20 border-blue-500 dark:border-blue-400 text-blue-600 dark:text-blue-400'
                          : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                      }`}
                    >
                      {i + 1}
                    </button>
                  ))}
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={page === totalPages}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {t('common.next')}
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default IntegrationsPage
