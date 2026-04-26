// candidate-api.repository.ts - Candidate and Party API repositories

import { ApiClient } from "../../../services/api-client.service";
import {
    Candidate,
    CreateCandidateRequest,
    CreatePartyRequest,
    Party,
    UpdateCandidateRequest,
    UpdatePartyRequest,
} from "../model/candidate.model";

const ELECTION_ROOT = "/election";
const PARTY_ROOT = "/party";

export class CandidateApiRepository {
    async listCandidates(electionId: string): Promise<Candidate[]> {
        return ApiClient.get<Candidate[]>(
            `${ELECTION_ROOT}/${electionId}/candidates`,
            { omitAuth: true },
        );
    }

    async createCandidate(
        electionId: string,
        body: CreateCandidateRequest,
    ): Promise<Candidate> {
        return ApiClient.post<Candidate>(
            `${ELECTION_ROOT}/${electionId}/candidates`,
            body,
        );
    }

    async updateCandidate(
        electionId: string,
        candidateId: string,
        body: UpdateCandidateRequest,
    ): Promise<Candidate> {
        return ApiClient.patch<Candidate>(
            `${ELECTION_ROOT}/${electionId}/candidates/${candidateId}`,
            body,
        );
    }
}

export class PartyApiRepository {
    async listParties(): Promise<Party[]> {
        return ApiClient.get<Party[]>(`${PARTY_ROOT}/`, { omitAuth: true });
    }

    async createParty(body: CreatePartyRequest): Promise<Party> {
        return ApiClient.post<Party>(`${PARTY_ROOT}/`, body);
    }

    async updateParty(partyId: string, body: UpdatePartyRequest): Promise<Party> {
        return ApiClient.patch<Party>(`${PARTY_ROOT}/${partyId}`, body);
    }

    async deleteParty(partyId: string): Promise<Party> {
        return ApiClient.delete<Party>(`${PARTY_ROOT}/${partyId}`);
    }

    async listDeletedParties(): Promise<Party[]> {
        return ApiClient.get<Party[]>(`${PARTY_ROOT}/deleted/all`);
    }

    async restoreParty(partyId: string): Promise<Party> {
        return ApiClient.patch<Party>(`${PARTY_ROOT}/${partyId}/restore`);
    }
}
