import type { SiteStatus } from "../types/api";

export function isProblem(
  status: SiteStatus | null,
  health?: string | null
): boolean {
  if (health) {
    return health === "critical" || health === "warning"
  }

  return (
    status === "DOWN" ||
    status === "ERROR" ||
    status === "TIMEOUT"
  )
}