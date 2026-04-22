export type SSLState =
  | "ok"
  | "warning"
  | "critical"
  | "invalid"
  | "no_data";

export type SiteStatus =
  | "UP"
  | "DOWN"
  | "TIMEOUT"
  | "ERROR"

export type SSLSeverity = "good" | "warn" | "bad"

export interface DashboardItem {
  site_id: string;
  name: string;
  url: string;
  last_status: SiteStatus | null;
  uptime_24h: number;
  uptime_7d: number;
  uptime_30d: number;
  check_interval: number;
  last_checked_at: string | null;
  is_active: boolean;
  ssl_valid?: boolean | null;
  ssl_days_left?: number | null;
  ssl_state?: SSLState;
  ssl_severity?: SSLSeverity;
  p95_latency?: number
  error_rate?: number
}

export interface Check {
  checked_at: string;
  bucket: string;
  status?: SiteStatus | null;
  response_time_ms: number | null;

  ssl_valid?: boolean | null;
  ssl_expires_at?: string | null;
  ssl_state?: SSLState;
  ssl_days_left?: number | null;
  ssl_severity?: SSLSeverity
}