// referendum.model.ts - Referendum model


export enum ReferendumScope {
    NATIONAL = "NATIONAL",
    REGIONAL = "REGIONAL",
    LOCAL = "LOCAL",
}

export enum ReferendumStatus {
    DRAFT = "DRAFT",
    OPEN = "OPEN",
    CLOSED = "CLOSED",
    CANCELLED = "CANCELLED",
}


export interface Referendum {
    id: string;
    title: string;
    question: string;
    description: string;
    scope: ReferendumScope;
    status: ReferendumStatus;
    voting_opens: string;
    voting_closes: string;
    constituency_ids: string[];
}

export interface CreateReferendumRequest {
    title: string;
    question: string;
    description: string;
    scope: ReferendumScope;
    status?: ReferendumStatus;
    constituency_ids?: string[];
    voting_opens?: string;
    voting_closes?: string;
}

export interface UpdateReferendumRequest {
    title?: string;
    question?: string;
    description?: string;
    scope?: string;
    status?: ReferendumStatus;
    voting_opens?: string;
    voting_closes?: string;
    is_active?: boolean;
    constituency_ids?: string[];
}