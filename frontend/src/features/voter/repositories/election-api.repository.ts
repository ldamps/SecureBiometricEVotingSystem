// election-api.repository.ts - Election API repository

import { ApiClient } from "../../../services/api-client.service";
import { Election, ElectionScope, ElectionStatus, ElectionType } from "../model/election.model";


const ROOT = "/election";

interface BackendElectionItem {
    id: string;
    title: string;
    election_type: ElectionType;
    scope: ElectionScope;
    allocation_method: string;
    status: ElectionStatus;
    voting_opens: string;
    voting_closes: string;
    created_by: string;
}

function mapElectionCore(b: BackendElectionItem): Election {
    return {
        id: b.id,
        title: b.title,
        election_type: b.election_type,
        scope: b.scope,
        allocation_method: b.allocation_method,
        status: b.status,
        voting_opens: b.voting_opens,
        voting_closes: b.voting_closes,
        created_by: b.created_by,
    };
}

export class ElectionApiRepository {

    async getElection(electionId: string): Promise<Election> {
        const raw = await ApiClient.get<BackendElectionItem>(`${ROOT}/${electionId}`);
        return mapElectionCore(raw);
    }

    async listElections(): Promise<Election[]> {
        // Backend route is defined as "/election/" (with trailing slash).
        const rows = await ApiClient.get<BackendElectionItem[]>(`${ROOT}/`);
        return rows.map(mapElectionCore);
    }

}