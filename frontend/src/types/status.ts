import type { SiteStatus } from "../types/api";

export function isProblem(status: SiteStatus | null): boolean {
  return (
    status === "DOWN" ||
    status === "ERROR" ||
    status === "TIMEOUT"
  );
}