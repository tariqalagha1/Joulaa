import api from './api'
import { AxiosResponse } from 'axios'

// Types
export interface Integration {
  id: string
  organization_id: string
  integration_type: string
  type?: string
  name: string
  description?: string
  configuration: Record<string, any>
  is_active: boolean
  last_sync_at?: string
  sync_status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  sync_error?: string
  metadata?: Record<string, any>
  health_check_url?: string
  last_health_check?: string
  health_status: 'healthy' | 'unhealthy' | 'unknown'
  created_at: string
  updated_at?: string
}

export interface IntegrationCreate {
  organization_id: string
  integration_type: string
  name: string
  description?: string
  configuration: Record<string, any>
  is_active?: boolean
  health_check_url?: string
  metadata?: Record<string, any>
}

export interface IntegrationUpdate {
  name?: string
  description?: string
  configuration?: Record<string, any>
  is_active?: boolean
  health_check_url?: string
  metadata?: Record<string, any>
}

export interface IntegrationListResponse {
  integrations: Integration[]
  total: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export interface IntegrationStats {
  total_integrations: number
  active_integrations: number
  healthy_integrations: number
  failed_syncs: number
  integrations_by_type: Record<string, number>
  recent_sync_errors: any[]
  sync_performance: Record<string, any>
  error_integrations?: number
}

export interface IntegrationSyncResponse {
  integration_id: string
  sync_started: boolean
  sync_status: string
  message: string
}

export interface IntegrationHealthCheck {
  integration_id: string
  health_status: string
  response_time?: number
  error_message?: string
  checked_at: string
  details?: Record<string, any>
  status?: string
  message?: string
}

export interface IntegrationTestResponse {
  success: boolean
  message: string
  response_time?: number
  test_results?: Record<string, any>
  error_details?: Record<string, any>
}

class IntegrationService {
  private readonly baseUrl = '/integrations'

  // List integrations with filtering and pagination
  async listIntegrations(params?: {
    query?: string
    integration_type?: string
    is_active?: boolean
    health_status?: string
    sync_status?: string
    organization_id?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
  type?: string
  }): Promise<IntegrationListResponse> {
    const response: AxiosResponse<IntegrationListResponse> = await api.get(this.baseUrl, { params })
    return response.data
  }

  // Create a new integration
  async createIntegration(integrationData: IntegrationCreate): Promise<Integration> {
    const response: AxiosResponse<Integration> = await api.post(this.baseUrl, integrationData)
    return response.data
  }

  // Get integration by ID
  async getIntegration(integrationId: string, includeOrganization?: boolean): Promise<Integration> {
    const params = includeOrganization ? { include_organization: true } : {}
    const response: AxiosResponse<Integration> = await api.get(`${this.baseUrl}/${integrationId}`, { params })
    return response.data
  }

  // Update integration
  async updateIntegration(integrationId: string, updateData: IntegrationUpdate): Promise<Integration> {
    const response: AxiosResponse<Integration> = await api.put(`${this.baseUrl}/${integrationId}`, updateData)
    return response.data
  }

  // Delete integration
  async deleteIntegration(integrationId: string, softDelete: boolean = true): Promise<void> {
    await api.delete(`${this.baseUrl}/${integrationId}`, {
      params: { soft_delete: softDelete }
    })
  }

  // Trigger integration synchronization
  async syncIntegration(integrationId: string, force: boolean = false): Promise<IntegrationSyncResponse> {
    const response: AxiosResponse<IntegrationSyncResponse> = await api.post(`${this.baseUrl}/${integrationId}/sync`, {
      force
    })
    return response.data
  }

  // Perform health check on integration
  async healthCheckIntegration(integrationId: string): Promise<IntegrationHealthCheck> {
    const response: AxiosResponse<IntegrationHealthCheck> = await api.post(`${this.baseUrl}/${integrationId}/health-check`)
    return response.data
  }

  async healthCheck(integrationId: string): Promise<IntegrationHealthCheck> {
    return this.healthCheckIntegration(integrationId)
  }

  // Test integration configuration
  async testIntegration(testData: {
    integration_type: string
    configuration: Record<string, any>
  }): Promise<IntegrationTestResponse> {
    const response: AxiosResponse<IntegrationTestResponse> = await api.post(`${this.baseUrl}/test`, testData)
    return response.data
  }

  // Get integration statistics
  async getIntegrationStats(organizationId?: string): Promise<IntegrationStats> {
    const params = organizationId ? { organization_id: organizationId } : {}
    const response: AxiosResponse<IntegrationStats> = await api.get(`${this.baseUrl}/stats`, { params })
    return response.data
  }

  // Bulk operations on integrations
  async bulkOperation(operation: string, integrationIds: string[], options?: Record<string, any>): Promise<any> {
    const response = await api.post(`${this.baseUrl}/bulk`, {
      operation,
      integration_ids: integrationIds,
      options: options || {}
    })
    return response.data
  }

  // Get available integration types
  async getIntegrationTypes(): Promise<{
    types: Array<{
      id: string
      name: string
      description: string
      category: string
      configuration_schema: Record<string, any>
      supported_features: string[]
    }>
  }> {
    const response = await api.get(`${this.baseUrl}/types`)
    return response.data
  }

  // Get integration logs
  async getIntegrationLogs(integrationId: string, params?: {
    level?: string
    date_from?: string
    date_to?: string
    page?: number
    page_size?: number
  }): Promise<{
    logs: Array<{
      id: string
      integration_id: string
      level: string
      message: string
      details?: Record<string, any>
      created_at: string
    }>
    total: number
    page: number
    page_size: number
  }> {
    const response = await api.get(`${this.baseUrl}/${integrationId}/logs`, { params })
    return response.data
  }

  // Get sync history
  async getSyncHistory(integrationId: string, params?: {
    status?: string
    date_from?: string
    date_to?: string
    page?: number
    page_size?: number
  }): Promise<{
    syncs: Array<{
      id: string
      integration_id: string
      status: string
      started_at: string
      completed_at?: string
      duration?: number
      records_processed?: number
      error_message?: string
      details?: Record<string, any>
    }>
    total: number
    page: number
    page_size: number
  }> {
    const response = await api.get(`${this.baseUrl}/${integrationId}/sync-history`, { params })
    return response.data
  }

  // Cancel running sync
  async cancelSync(integrationId: string): Promise<void> {
    await api.post(`${this.baseUrl}/${integrationId}/cancel-sync`)
  }

  // Export integration configuration
  async exportIntegration(integrationId: string): Promise<any> {
    const response = await api.get(`${this.baseUrl}/${integrationId}/export`)
    return response.data
  }

  // Import integration configuration
  async importIntegration(configData: any): Promise<Integration> {
    const response: AxiosResponse<Integration> = await api.post(`${this.baseUrl}/import`, configData)
    return response.data
  }

  // Get integration metrics
  async getIntegrationMetrics(integrationId: string, params?: {
    metric_type?: string
    date_from?: string
    date_to?: string
    granularity?: 'hour' | 'day' | 'week' | 'month'
  }): Promise<{
    metrics: Array<{
      timestamp: string
      value: number
      metric_type: string
    }>
    summary: Record<string, any>
  }> {
    const response = await api.get(`${this.baseUrl}/${integrationId}/metrics`, { params })
    return response.data
  }

  // Validate integration configuration
  async validateConfiguration(integrationType: string, configuration: Record<string, any>): Promise<{
    valid: boolean
    errors: string[]
    warnings: string[]
  }> {
    const response = await api.post(`${this.baseUrl}/validate`, {
      integration_type: integrationType,
      configuration
    })
    return response.data
  }
}

export const integrationService = new IntegrationService()
export default integrationService
