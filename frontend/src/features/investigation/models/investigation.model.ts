// investigation.model.ts - Investigation and error report models.

export interface Investigation {
    id: string;
    error_id: string;
    election_id: string;
    referendum_id: string;
    raised_by: string;
    title: string;
    description: string;
    severity: string;
    status: string;
    category: string;
    assigned_to: string;
    notes: string;
    resolved_by: string;
    resolution_summary: string;
    raised_at: string;
    resolved_at: string;
}

export interface ErrorReport {
    id: string;
    election_id: string;
    referendum_id: string;
    reported_by: string;
    title: string;
    description: string;
    severity: string;
    reported_at: string;
}

export interface CreateErrorReportRequest {
    election_id?: string;
    referendum_id?: string;
    reported_by?: string;
    title: string;
    description?: string;
    severity: string;
}

export interface ErrorReportWithInvestigation {
    error_report: ErrorReport;
    investigation: Investigation;
}

export interface UpdateInvestigationRequest {
    status?: string;
    category?: string;
    assigned_to?: string;
    notes?: string;
    resolved_by?: string;
    resolution_summary?: string;
}
