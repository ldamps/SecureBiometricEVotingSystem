// candidate.model.ts - Candidate and party models

export interface Candidate {
    id: string;
    election_id: string;
    constituency_id: string;
    first_name: string;
    last_name: string;
    party_id: string;
    is_active: boolean;
}

export interface Party {
    id: string;
    party_name: string;
    abbreviation?: string;
    is_active: boolean;
}

export interface CreateCandidateRequest {
    constituency_id: string;
    first_name: string;
    last_name: string;
    party_id: string;
}

export interface UpdateCandidateRequest {
    first_name?: string;
    last_name?: string;
    is_active?: boolean;
}

export interface CreatePartyRequest {
    party_name: string;
    abbreviation?: string;
    is_active?: boolean;
}

export interface UpdatePartyRequest {
    party_name?: string;
    abbreviation?: string;
    is_active?: boolean;
}
