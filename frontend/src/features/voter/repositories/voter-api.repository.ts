// voter-api.repository.ts - Voter API repository

import { ApiClient } from "../../../services/api-client.service";
import {
    Address,
    AddressStatus,
    AddressType,
    CreateAddressRequest,
    CreatePassportRequest,
    CreateVoterLedgerRequest,
    ImmigrationStatus,
    NationalityCategory,
    Passport,
    UpdateAddressRequest,
    UpdatePassportRequest,
    VerifyIdentityRequest,
    VerifyIdentityResponse,
    Voter,
    VoterCreateRequest,
    VoterDetail,
    VoterLedgerItem,
    VoterUpdateRequest,
} from "../model/voter.model";

const ROOT = "/voter";

interface BackendPassport {
    id: string;
    passport_number?: string | null;
    issuing_country?: string | null;
    expiry_date?: string | null;
    is_primary: boolean;
}

/** Address JSON from the API (`town` is the city field). */
interface BackendAddressItem {
    id: string;
    address_type?: string | null;
    address_line1?: string | null;
    address_line2?: string | null;
    town?: string | null;
    postcode?: string | null;
    county?: string | null;
    country?: string | null;
    address_status?: string | null;
    renew_by?: string | null;
}

interface BackendVoterItem {
    id: string;
    national_insurance_number?: string | null;
    first_name?: string | null;
    surname?: string | null;
    previous_first_name?: string | null;
    previous_surname?: string | null;
    date_of_birth?: string | null;
    email?: string | null;
    voter_reference?: string | null;
    constituency_id?: string | null;
    nationality_category: NationalityCategory;
    immigration_status?: ImmigrationStatus | null;
    immigration_status_expiry?: string | null;
    voter_status?: string | null;
    registration_status: string;
    failed_auth_attempts: number;
    locked_until?: string | null;
    registered_at?: string | null;
    renew_by?: string | null;
    passports: BackendPassport[];
}

interface BackendVoterLedger {
    id: string;
    voter_id: string;
    election_id?: string | null;
    referendum_id?: string | null;
    voted_at?: string | null;
}

function definedPayload(
    entries: Record<string, unknown | undefined>,
): Record<string, unknown> {
    return Object.fromEntries(
        Object.entries(entries).filter(([, v]) => v !== undefined),
    );
}

function mapPassport(p: BackendPassport): Passport {
    return {
        id: p.id,
        passport_number: p.passport_number ?? "",
        issuing_country: p.issuing_country ?? "",
        expiry_date: p.expiry_date ?? "",
        is_primary: p.is_primary,
    };
}

function mapAddress(b: BackendAddressItem): Address {
    return {
        id: b.id,
        address_type: b.address_type
            ? (b.address_type as AddressType)
            : undefined,
        address_line1: b.address_line1 ?? "",
        address_line2: b.address_line2 ?? undefined,
        city: b.town ?? "",
        postcode: b.postcode ?? "",
        county: b.county ?? "",
        country: b.country ?? "",
        address_status:
            (b.address_status as AddressStatus) ?? AddressStatus.PENDING,
        renew_by: b.renew_by ?? undefined,
    };
}

function mapVoterCore(b: BackendVoterItem): Voter {
    return {
        id: b.id,
        national_insurance_number: b.national_insurance_number ?? undefined,
        first_name: b.first_name ?? "",
        surname: b.surname ?? "",
        previous_first_name: b.previous_first_name ?? undefined,
        previous_surname: b.previous_surname ?? undefined,
        date_of_birth: b.date_of_birth ?? "",
        email: b.email ?? "",
        voter_reference: b.voter_reference ?? "",
        constituency_id: b.constituency_id ?? "",
        nationality_category: b.nationality_category,
        immigration_status: b.immigration_status ?? undefined,
        immigration_status_expiry: b.immigration_status_expiry ?? undefined,
        voter_status: b.voter_status ?? "PENDING",
        registration_status: b.registration_status,
        failed_auth_attempts: b.failed_auth_attempts,
        locked_until: b.locked_until ?? undefined,
        registered_at: b.registered_at ?? undefined,
        renew_by: b.renew_by ?? undefined,
    };
}

function mapVoterDetail(b: BackendVoterItem): VoterDetail {
    return {
        ...mapVoterCore(b),
        passports: (b.passports ?? []).map(mapPassport),
    };
}

function mapLedger(row: BackendVoterLedger): VoterLedgerItem {
    return {
        id: row.id,
        voter_id: row.voter_id,
        election_id: row.election_id ?? undefined,
        referendum_id: row.referendum_id ?? undefined,
        voted_at: row.voted_at ?? undefined,
    };
}

/** Convert dd/mm/yyyy to ISO datetime string for the backend. Works for any date field. */
function dateToISO(dob: string): string {
    const parts = dob.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (parts) {
        const [, dd, mm, yyyy] = parts;
        return `${yyyy}-${mm}-${dd}T00:00:00Z`;
    }
    return dob; // already ISO or unknown format — pass through
}

function registrationBody(req: VoterCreateRequest): Record<string, unknown> {
    return {
        kyc_session_id: req.kyc_session_id,
        first_name: req.first_name,
        surname: req.surname,
        previous_first_name: req.previous_first_name,
        previous_surname: req.previous_surname,
        date_of_birth: dateToISO(req.date_of_birth),
        email: req.email,
        national_insurance_number: req.national_insurance_number,
        passports: req.passports.map((p) =>
            definedPayload({
                passport_number: p.passport_number,
                issuing_country: p.issuing_country,
                expiry_date: p.expiry_date ? dateToISO(p.expiry_date) : undefined,
                is_primary: p.is_primary,
            }),
        ),
        nationality_category: req.nationality_category,
        immigration_status: req.immigration_status,
        immigration_status_expiry: req.immigration_status_expiry,
        renew_by: req.renew_by,
    };
}

function updateVoterBody(req: VoterUpdateRequest): Record<string, unknown> {
    return definedPayload({
        first_name: req.first_name,
        surname: req.surname,
        previous_first_name: req.previous_first_name,
        previous_surname: req.previous_surname,
        date_of_birth: req.date_of_birth,
        email: req.email,
        nationality_category: req.nationality_category,
        immigration_status: req.immigration_status,
        immigration_status_expiry: req.immigration_status_expiry,
        renew_by: req.renew_by,
    });
}

function createAddressBody(req: CreateAddressRequest): Record<string, unknown> {
    return definedPayload({
        address_type: req.address_type,
        address_line1: req.address_line1,
        address_line2: req.address_line2,
        town: req.city,
        postcode: req.postcode,
        county: req.county,
        country: req.country,
        renew_by: req.renew_by,
    });
}

function updateAddressBody(req: UpdateAddressRequest): Record<string, unknown> {
    return definedPayload({
        address_type: req.address_type,
        address_line1: req.address_line1,
        address_line2: req.address_line2,
        town: req.city,
        postcode: req.postcode,
        county: req.county,
        country: req.country,
        address_status: req.address_status,
        renew_by: req.renew_by,
    });
}

function createPassportBody(req: CreatePassportRequest): Record<string, unknown> {
    return definedPayload({
        passport_number: req.passport_number,
        issuing_country: req.issuing_country,
        expiry_date: req.expiry_date ? dateToISO(req.expiry_date) : undefined,
        is_primary: req.is_primary,
    });
}

function updatePassportBody(req: UpdatePassportRequest): Record<string, unknown> {
    return definedPayload({
        passport_number: req.passport_number,
        issuing_country: req.issuing_country,
        expiry_date: req.expiry_date ? dateToISO(req.expiry_date) : undefined,
        is_primary: req.is_primary,
    });
}

export class VoterApiRepository {
    async getVoter(voterId: string): Promise<VoterDetail> {
        const raw = await ApiClient.get<BackendVoterItem>(`${ROOT}/${voterId}`);
        return mapVoterDetail(raw);
    }

    async registerVoter(body: VoterCreateRequest): Promise<VoterDetail> {
        const raw = await ApiClient.post<BackendVoterItem>(
            `${ROOT}/register`,
            registrationBody(body),
        );
        return mapVoterDetail(raw);
    }

    async updateVoter(
        voterId: string,
        body: VoterUpdateRequest,
    ): Promise<VoterDetail> {
        const raw = await ApiClient.patch<BackendVoterItem>(
            `${ROOT}/${voterId}`,
            updateVoterBody(body),
        );
        return mapVoterDetail(raw);
    }

    async verifyIdentity(
        body: VerifyIdentityRequest,
    ): Promise<VerifyIdentityResponse> {
        return ApiClient.post<VerifyIdentityResponse>(
            `${ROOT}/verify-identity`,
            body,
        );
    }

    async listAddresses(voterId: string): Promise<Address[]> {
        const rows = await ApiClient.get<BackendAddressItem[]>(
            `${ROOT}/${voterId}/addresses`,
        );
        return rows.map(mapAddress);
    }

    async getAddress(
        voterId: string,
        addressId: string,
    ): Promise<Address> {
        const raw = await ApiClient.get<BackendAddressItem>(
            `${ROOT}/${voterId}/address/${addressId}`,
        );
        return mapAddress(raw);
    }

    async createAddress(
        voterId: string,
        body: CreateAddressRequest,
    ): Promise<Address> {
        const raw = await ApiClient.post<BackendAddressItem>(
            `${ROOT}/${voterId}/address`,
            createAddressBody(body),
        );
        return mapAddress(raw);
    }

    async updateAddress(
        voterId: string,
        addressId: string,
        body: UpdateAddressRequest,
    ): Promise<Address> {
        const raw = await ApiClient.patch<BackendAddressItem>(
            `${ROOT}/${voterId}/address/${addressId}`,
            updateAddressBody(body),
        );
        return mapAddress(raw);
    }

    async deleteAddress(
        voterId: string,
        addressId: string,
    ): Promise<void> {
        await ApiClient.delete(`${ROOT}/${voterId}/address/${addressId}`);
    }

    async listPassports(voterId: string): Promise<Passport[]> {
        const rows = await ApiClient.get<BackendPassport[]>(
            `${ROOT}/${voterId}/passports`,
        );
        return rows.map(mapPassport);
    }

    async getPassport(
        voterId: string,
        passportId: string,
    ): Promise<Passport> {
        const raw = await ApiClient.get<BackendPassport>(
            `${ROOT}/${voterId}/passport/${passportId}`,
        );
        return mapPassport(raw);
    }

    async createPassport(
        voterId: string,
        body: CreatePassportRequest,
    ): Promise<Passport> {
        const raw = await ApiClient.post<BackendPassport>(
            `${ROOT}/${voterId}/passport`,
            createPassportBody(body),
        );
        return mapPassport(raw);
    }

    async updatePassport(
        voterId: string,
        passportId: string,
        body: UpdatePassportRequest,
    ): Promise<Passport> {
        const raw = await ApiClient.patch<BackendPassport>(
            `${ROOT}/${voterId}/passport/${passportId}`,
            updatePassportBody(body),
        );
        return mapPassport(raw);
    }

    async deletePassport(
        voterId: string,
        passportId: string,
    ): Promise<void> {
        await ApiClient.delete(`${ROOT}/${voterId}/passport/${passportId}`);
    }

    async getLedgerEntry(
        voterId: string,
        ledgerId: string,
    ): Promise<VoterLedgerItem> {
        const raw = await ApiClient.get<BackendVoterLedger>(
            `${ROOT}/${voterId}/ledger/${ledgerId}`,
        );
        return mapLedger(raw);
    }

    async listLedgerEntries(voterId: string): Promise<VoterLedgerItem[]> {
        const rows = await ApiClient.get<BackendVoterLedger[]>(
            `${ROOT}/${voterId}/ledger`,
        );
        return rows.map(mapLedger);
    }

    async createLedgerEntry(
        voterId: string,
        body: CreateVoterLedgerRequest,
    ): Promise<VoterLedgerItem> {
        const raw = await ApiClient.post<BackendVoterLedger>(
            `${ROOT}/${voterId}/ledger`,
            definedPayload({
                election_id: body.election_id,
                voted_at: body.voted_at,
            }),
        );
        return mapLedger(raw);
    }
}
