// investigation-api.repository.ts - Error report and investigation API repository.

import { ApiClient } from "../../../services/api-client.service";
import {
    Investigation,
    ErrorReport,
    CreateErrorReportRequest,
    ErrorReportWithInvestigation,
    UpdateInvestigationRequest,
} from "../models/investigation.model";

const ROOT = "/errors";

interface BackendInvestigationItem {
    id: string;
    error_id?: string | null;
    election_id?: string | null;
    referendum_id?: string | null;
    raised_by?: string | null;
    title: string;
    description?: string | null;
    severity: string;
    status: string;
    category?: string | null;
    assigned_to?: string | null;
    notes?: string | null;
    resolved_by?: string | null;
    resolution_summary?: string | null;
    raised_at?: string | null;
    resolved_at?: string | null;
}

interface BackendErrorReportItem {
    id: string;
    election_id?: string | null;
    referendum_id?: string | null;
    reported_by?: string | null;
    title: string;
    description?: string | null;
    severity: string;
    reported_at?: string | null;
}

interface BackendErrorReportWithInvestigation {
    error_report: BackendErrorReportItem;
    investigation: BackendInvestigationItem;
}

function mapInvestigation(b: BackendInvestigationItem): Investigation {
    return {
        id: b.id,
        error_id: b.error_id ?? "",
        election_id: b.election_id ?? "",
        referendum_id: b.referendum_id ?? "",
        raised_by: b.raised_by ?? "",
        title: b.title,
        description: b.description ?? "",
        severity: b.severity,
        status: b.status,
        category: b.category ?? "",
        assigned_to: b.assigned_to ?? "",
        notes: b.notes ?? "",
        resolved_by: b.resolved_by ?? "",
        resolution_summary: b.resolution_summary ?? "",
        raised_at: b.raised_at ?? "",
        resolved_at: b.resolved_at ?? "",
    };
}

function mapErrorReport(b: BackendErrorReportItem): ErrorReport {
    return {
        id: b.id,
        election_id: b.election_id ?? "",
        referendum_id: b.referendum_id ?? "",
        reported_by: b.reported_by ?? "",
        title: b.title,
        description: b.description ?? "",
        severity: b.severity,
        reported_at: b.reported_at ?? "",
    };
}

export class InvestigationApiRepository {
    async createErrorReport(body: CreateErrorReportRequest): Promise<ErrorReportWithInvestigation> {
        const raw = await ApiClient.post<BackendErrorReportWithInvestigation>(
            `${ROOT}/report`,
            body,
        );
        return {
            error_report: mapErrorReport(raw.error_report),
            investigation: mapInvestigation(raw.investigation),
        };
    }

    async getErrorReport(reportId: string): Promise<ErrorReport> {
        const raw = await ApiClient.get<BackendErrorReportItem>(`${ROOT}/report/${reportId}`);
        return mapErrorReport(raw);
    }

    async getReportsByElection(electionId: string): Promise<ErrorReport[]> {
        const rows = await ApiClient.get<BackendErrorReportItem[]>(`${ROOT}/report/election/${electionId}`);
        return rows.map(mapErrorReport);
    }

    async getReportsByReferendum(referendumId: string): Promise<ErrorReport[]> {
        const rows = await ApiClient.get<BackendErrorReportItem[]>(`${ROOT}/report/referendum/${referendumId}`);
        return rows.map(mapErrorReport);
    }

    async getInvestigation(investigationId: string): Promise<Investigation> {
        const raw = await ApiClient.get<BackendInvestigationItem>(`${ROOT}/${investigationId}`);
        return mapInvestigation(raw);
    }

    async getInvestigationsByElection(electionId: string): Promise<Investigation[]> {
        const rows = await ApiClient.get<BackendInvestigationItem[]>(`${ROOT}/investigations/${electionId}`);
        return rows.map(mapInvestigation);
    }

    async getInvestigationsByReferendum(referendumId: string): Promise<Investigation[]> {
        const rows = await ApiClient.get<BackendInvestigationItem[]>(`${ROOT}/investigations/referendum/${referendumId}`);
        return rows.map(mapInvestigation);
    }

    async getInvestigationsByAssignee(officialId: string): Promise<Investigation[]> {
        const rows = await ApiClient.get<BackendInvestigationItem[]>(`${ROOT}/investigation/${officialId}/assigned`);
        return rows.map(mapInvestigation);
    }

    async updateInvestigation(investigationId: string, body: UpdateInvestigationRequest): Promise<Investigation> {
        const raw = await ApiClient.patch<BackendInvestigationItem>(`${ROOT}/investigation/${investigationId}`, body);
        return mapInvestigation(raw);
    }
}
