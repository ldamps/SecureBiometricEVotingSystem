// referendum-api.repository.ts - Referendum API repository

import { ApiClient } from "../../../services/api-client.service";
import { isWithinScheduledVotingWindow } from "../../../utils/voting-window";
import {
    Referendum,
    ReferendumScope,
    ReferendumStatus,
    CreateReferendumRequest,
    UpdateReferendumRequest,
} from "../model/referendum.model";

const ROOT = "/referendum";

interface BackendReferendumItem {
    id: string;
    title: string;
    question: string;
    description: string;
    scope: ReferendumScope;
    status: ReferendumStatus;
    voting_opens: string;
    voting_closes: string;
}

function mapReferendumCore(b: BackendReferendumItem): Referendum {
    return {
        id: b.id,
        title: b.title,
        question: b.question,
        description: b.description,
        scope: b.scope,
        status: b.status,
        voting_opens: b.voting_opens,
        voting_closes: b.voting_closes,
    }
}

function definedPayload(
    entries: Record<string, unknown | undefined>,
): Record<string, unknown> {
    return Object.fromEntries(
        Object.entries(entries).filter(([, value]) => value !== undefined),
    );
}

function createReferendumBody(body: CreateReferendumRequest): Record<string, unknown> {
    return definedPayload({
        title: body.title,
        question: body.question,
        description: body.description,
        scope: body.scope,
        voting_opens: body.voting_opens,
        voting_closes: body.voting_closes,
    });
}

function updateReferendumBody(body: UpdateReferendumRequest): Record<string, unknown> {
    return definedPayload({
        question: body.question,
        description: body.description,
        status: body.status,
        voting_opens: body.voting_opens,
        voting_closes: body.voting_closes,
        is_active: body.is_active,
    });
}

export class ReferendumApiRepository {
    async getReferendum(referendumId: string): Promise<Referendum> {
        const raw = await ApiClient.get<BackendReferendumItem>(`${ROOT}/${referendumId}`);
        return mapReferendumCore(raw);
    }

    async listReferendums(): Promise<Referendum[]> {
        const rows = await ApiClient.get<BackendReferendumItem[]>(`${ROOT}/`, {
            omitAuth: true,
        });
        return rows.map(mapReferendumCore);
    }

    async createReferendum(body: CreateReferendumRequest): Promise<Referendum> {
        const raw = await ApiClient.post<BackendReferendumItem>(`${ROOT}/`, createReferendumBody(body));
        return mapReferendumCore(raw);
    }
    
    async updateReferendum(referendumId: string, body: UpdateReferendumRequest): Promise<Referendum> {
        const raw = await ApiClient.patch<BackendReferendumItem>(`${ROOT}/${referendumId}`, updateReferendumBody(body));
        return mapReferendumCore(raw);
    }

    async listOpenReferendums(): Promise<Referendum[]> {
        const referendums = await this.listReferendums();
        return referendums.filter(
            (referendum) =>
                referendum.status === ReferendumStatus.OPEN &&
                isWithinScheduledVotingWindow(referendum.voting_opens, referendum.voting_closes),
        );
    }
}