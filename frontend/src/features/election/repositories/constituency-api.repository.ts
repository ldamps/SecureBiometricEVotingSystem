// constituency-api.repository.ts - Constituency API repository (read-only).

import { ApiClient } from "../../../services/api-client.service";
import { Constituency } from "../model/constituency.model";

const ROOT = "/constituency";

interface BackendConstituencyItem {
    id: string;
    name: string;
    country: string;
    county?: string | null;
    region?: string | null;
    is_active: boolean;
}

function mapConstituency(b: BackendConstituencyItem): Constituency {
    return {
        id: b.id,
        name: b.name,
        country: b.country,
        county: b.county ?? "",
        region: b.region ?? "",
        is_active: b.is_active,
    };
}

export class ConstituencyApiRepository {
    async listConstituencies(): Promise<Constituency[]> {
        const rows = await ApiClient.get<BackendConstituencyItem[]>(`${ROOT}`, {
            omitAuth: true,
        });
        return rows.map(mapConstituency);
    }

    async getConstituency(constituencyId: string): Promise<Constituency> {
        const raw = await ApiClient.get<BackendConstituencyItem>(
            `${ROOT}/${constituencyId}`,
            { omitAuth: true },
        );
        return mapConstituency(raw);
    }
}
