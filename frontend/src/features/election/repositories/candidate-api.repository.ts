// candidate-api.repository.ts - Candidate and Party API repository

import { ApiClient } from "../../../services/api-client.service";
import { Candidate, Party } from "../model/candidate.model";

const ELECTION_ROOT = "/election";
const PARTY_ROOT = "/party";

export class CandidateApiRepository {
    async listCandidates(electionId: string): Promise<Candidate[]> {
        return ApiClient.get<Candidate[]>(
            `${ELECTION_ROOT}/${electionId}/candidates`,
            { omitAuth: true },
        );
    }
}

export class PartyApiRepository {
    async listParties(): Promise<Party[]> {
        return ApiClient.get<Party[]>(`${PARTY_ROOT}/`, { omitAuth: true });
    }
}
