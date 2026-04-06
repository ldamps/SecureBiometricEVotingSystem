// constituency.model.ts - Constituency model (read-only).

export interface Constituency {
    id: string;
    name: string;
    country: string;
    county: string;
    region: string;
    is_active: boolean;
}
