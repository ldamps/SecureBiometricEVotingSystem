// Official model

export enum OfficialRole {
    ADMIN = "ADMIN",
    OFFICER = "OFFICER",
}

export interface Official {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
    email: string;
    role: OfficialRole;
    is_active: boolean;
}

export interface CreateOfficialRequest {
    username: string;
    first_name: string;
    last_name: string;
    email: string;
    role: OfficialRole;
    created_by: string;
}

export interface UpdateOfficialRequest {
    first_name: string;
    last_name: string;
    email: string;
    role: OfficialRole;
    is_active: boolean;
}