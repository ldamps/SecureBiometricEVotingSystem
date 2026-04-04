// Official API repository

import { ApiClient } from "../../../services/api-client.service";
import { Official, OfficialRole, CreateOfficialRequest, UpdateOfficialRequest } from "../model/official.model";

const ROOT = "/official";

interface BackendOfficialItem {
    id: string;
    username: string;
    first_name?: string | null;
    last_name?: string | null;
    email?: string | null;
    role: OfficialRole;
    is_active: boolean;
    must_reset_password: boolean;
    failed_login_attempts: number;
    created_by?: string | null;
    last_login_at?: string | null;
    locked_until?: string | null;
}

function mapOfficialCore(b: BackendOfficialItem): Official {
    return {
        id: b.id,
        username: b.username,
        first_name: b.first_name ?? "",
        last_name: b.last_name ?? "",
        email: b.email ?? "",
        role: b.role,
    };
}

function definedPayload(
    entries: Record<string, unknown | undefined>,
): Record<string, unknown> {
    return Object.fromEntries(
        Object.entries(entries).filter(([, value]) => value !== undefined),
    );
}

function createOfficialBody(body: CreateOfficialRequest): Record<string, unknown> {
    return definedPayload({
        username: body.username,
        first_name: body.first_name,
        last_name: body.last_name,
        email: body.email,
        role: body.role,
    });
}

function updateOfficialBody(body: UpdateOfficialRequest): Record<string, unknown> {
    return definedPayload({
        first_name: body.first_name,
        last_name: body.last_name,
        email: body.email,
        role: body.role,
        is_active: body.is_active,
    });
}

export class OfficialApiRepository {
    async getOfficial(officialId: string): Promise<Official> {
        const raw = await ApiClient.get<BackendOfficialItem>(`${ROOT}/${officialId}`);
        return mapOfficialCore(raw);
    }

    async listOfficials(): Promise<Official[]> {
        const rows = await ApiClient.get<BackendOfficialItem[]>(`${ROOT}/`, {
            omitAuth: true,
        });
        return rows.map(mapOfficialCore);
    }

    async createOfficial(body: CreateOfficialRequest): Promise<Official> {
        const raw = await ApiClient.post<BackendOfficialItem>(`${ROOT}/`, createOfficialBody(body));
        return mapOfficialCore(raw);
    }

    async updateOfficial(officialId: string, body: UpdateOfficialRequest): Promise<Official> {
        const raw = await ApiClient.patch<BackendOfficialItem>(`${ROOT}/${officialId}`, updateOfficialBody(body));
        return mapOfficialCore(raw);
    }

    async deactivateOfficial(officialId: string): Promise<Official> {
        const raw = await ApiClient.patch<BackendOfficialItem>(`${ROOT}/${officialId}/deactivate`);
        return mapOfficialCore(raw);
    }

    async activateOfficial(officialId: string): Promise<Official> {
        const raw = await ApiClient.patch<BackendOfficialItem>(`${ROOT}/${officialId}/activate`);
        return mapOfficialCore(raw);
    }
}