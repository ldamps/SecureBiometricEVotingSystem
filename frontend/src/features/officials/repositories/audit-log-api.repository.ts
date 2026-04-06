// audit-log-api.repository.ts - Audit log API repository (admin-only endpoints).

import { ApiClient } from "../../../services/api-client.service";
import { AuditLog } from "../model/audit-log.model";
import type { ElectionAuditReport, ReferendumAuditReport } from "../model/audit-report.model";

const ROOT = "/audit";

interface BackendAuditLogItem {
    id: string;
    event_type: string;
    action: string;
    summary: string;
    actor_id?: string | null;
    actor_type?: string | null;
    resource_type?: string | null;
    resource_id?: string | null;
    election_id?: string | null;
    referendum_id?: string | null;
    event_metadata?: Record<string, unknown> | null;
    created_at?: string | null;
}

function mapAuditLog(b: BackendAuditLogItem): AuditLog {
    return {
        id: b.id,
        event_type: b.event_type,
        action: b.action,
        summary: b.summary,
        actor_id: b.actor_id ?? "",
        actor_type: b.actor_type ?? "",
        resource_type: b.resource_type ?? "",
        resource_id: b.resource_id ?? "",
        election_id: b.election_id ?? "",
        referendum_id: b.referendum_id ?? "",
        event_metadata: b.event_metadata ?? null,
        created_at: b.created_at ?? "",
    };
}

export class AuditLogApiRepository {
    async getRecentAuditLogs(limit: number = 50): Promise<AuditLog[]> {
        const rows = await ApiClient.get<BackendAuditLogItem[]>(
            `${ROOT}/`,
            { params: { limit: String(limit) } },
        );
        return rows.map(mapAuditLog);
    }

    async getAuditLogsByElection(electionId: string): Promise<AuditLog[]> {
        const rows = await ApiClient.get<BackendAuditLogItem[]>(
            `${ROOT}/election/${electionId}`,
        );
        return rows.map(mapAuditLog);
    }

    async getAuditLogsByReferendum(referendumId: string): Promise<AuditLog[]> {
        const rows = await ApiClient.get<BackendAuditLogItem[]>(
            `${ROOT}/referendum/${referendumId}`,
        );
        return rows.map(mapAuditLog);
    }

    async getAuditLogsByDateRange(start?: string, end?: string, electionId?: string): Promise<AuditLog[]> {
        const params: Record<string, string> = {};
        if (start) params.start = start;
        if (end) params.end = end;
        if (electionId) params.election_id = electionId;
        const rows = await ApiClient.get<BackendAuditLogItem[]>(
            `${ROOT}/date-range`,
            { params },
        );
        return rows.map(mapAuditLog);
    }

    async getAuditLogById(auditId: string): Promise<AuditLog> {
        const raw = await ApiClient.get<BackendAuditLogItem>(`${ROOT}/${auditId}`);
        return mapAuditLog(raw);
    }

    async getElectionAuditReport(electionId: string): Promise<ElectionAuditReport> {
        return ApiClient.get<ElectionAuditReport>(`${ROOT}/report/election/${electionId}`);
    }

    async getReferendumAuditReport(referendumId: string): Promise<ReferendumAuditReport> {
        return ApiClient.get<ReferendumAuditReport>(`${ROOT}/report/referendum/${referendumId}`);
    }
}
