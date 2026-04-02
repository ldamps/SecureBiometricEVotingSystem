// election-api.repository.ts - Election API repository

import { ApiClient } from "../../../services/api-client.service";
import { isWithinScheduledVotingWindow } from "../../../utils/voting-window";
import {
  AllocationMethod,
  CreateElectionRequest,
  Election,
  ElectionScope,
  ElectionStatus,
  ElectionType,
  UpdateElectionRequest,
} from "../model/election.model";


const ROOT = "/election";

interface BackendElectionItem {
  id: string;
  title: string;
  election_type: ElectionType;
  scope: ElectionScope;
  allocation_method: string;
  status: ElectionStatus;
  voting_opens?: string | null;
  voting_closes?: string | null;
  created_by?: string | null;
}

function mapElectionCore(b: BackendElectionItem): Election {
  return {
    id: b.id,
    title: b.title,
    election_type: b.election_type,
    scope: b.scope,
    allocation_method: b.allocation_method as AllocationMethod,
    status: b.status,
    voting_opens: b.voting_opens ?? undefined,
    voting_closes: b.voting_closes ?? undefined,
    created_by: b.created_by ?? undefined,
  };
}

function definedPayload(
  entries: Record<string, unknown | undefined>,
): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(entries).filter(([, value]) => value !== undefined),
  );
}

function createElectionBody(body: CreateElectionRequest): Record<string, unknown> {
  return definedPayload({
    title: body.title,
    election_type: body.election_type,
    scope: body.scope,
    voting_opens: body.voting_opens,
    voting_closes: body.voting_closes,
    created_by: body.created_by,
  });
}

function updateElectionBody(body: UpdateElectionRequest): Record<string, unknown> {
  return definedPayload({
    status: body.status,
    voting_opens: body.voting_opens,
    voting_closes: body.voting_closes,
  });
}

export class ElectionApiRepository {
  async getElection(electionId: string): Promise<Election> {
    const raw = await ApiClient.get<BackendElectionItem>(`${ROOT}/${electionId}`);
    return mapElectionCore(raw);
  }

  async listElections(): Promise<Election[]> {
    // Backend route is defined as "/election/" (with trailing slash).
    const rows = await ApiClient.get<BackendElectionItem[]>(`${ROOT}/`, {
      omitAuth: true,
    });
    return rows.map(mapElectionCore);
  }

  async createElection(body: CreateElectionRequest): Promise<Election> {
    const raw = await ApiClient.post<BackendElectionItem>(
      `${ROOT}/`,
      createElectionBody(body),
    );
    return mapElectionCore(raw);
  }

  async updateElection(
    electionId: string,
    body: UpdateElectionRequest,
  ): Promise<Election> {
    const raw = await ApiClient.patch<BackendElectionItem>(
      `${ROOT}/${electionId}`,
      updateElectionBody(body),
    );
    return mapElectionCore(raw);
  }

  async listOpenElections(): Promise<Election[]> {
    const elections = await this.listElections();
    return elections.filter(
      (election) =>
        election.status === ElectionStatus.OPEN &&
        isWithinScheduledVotingWindow(election.voting_opens, election.voting_closes),
    );
  }
}