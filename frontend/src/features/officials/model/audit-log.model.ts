// audit-log.model.ts - Audit log model.

export interface AuditLog {
    id: string;
    event_type: string;
    action: string;
    summary: string;
    actor_id: string;
    actor_type: string;
    resource_type: string;
    resource_id: string;
    election_id: string;
    referendum_id: string;
    event_metadata: Record<string, unknown> | null;
    created_at: string;
}
