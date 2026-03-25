// Voter models - Based on the backend models

export enum VoterStatus {
    /** 
    Voter status.
    ** PENDING ** - Voter has not been verified.
    ** SUSPENDED ** - Voter has been suspended due to too many failed authentication attempts.
    ** ACTIVE ** - Voter is active and can vote.
    */
    PENDING = "PENDING",
    SUSPENDED = "SUSPENDED",
    ACTIVE = "ACTIVE",
}

export enum NationalityCategory {
    /**
    Nationality category.
    ** BRITISH_CITIZEN ** - Voter is a British citizen.
    ** IRISH_CITIZEN ** - Voter is an Irish citizen.
    ** COMMONWEALTH_SETTLED ** - Voter is a citizen of a Commonwealth country that has settled in the UK.
    ** COMMONWEALTH_LEAVE_TO_REMAIN ** - Voter is a citizen of a Commonwealth country that has leave to remain in the UK.
    ** EU_RETAINED_RIGHTS ** - Voter is a citizen of an EU country that has retained rights in the UK.
    ** OTHER ** - Voter is a citizen of a non-EU country.
    */
    BRITISH_CITIZEN = "BRITISH_CITIZEN",
    IRISH_CITIZEN = "IRISH_CITIZEN",
    COMMONWEALTH_SETTLED = "COMMONWEALTH_SETTLED",
    COMMONWEALTH_LEAVE_TO_REMAIN = "COMMONWEALTH_LEAVE_TO_REMAIN",
    EU_RETAINED_RIGHTS = "EU_RETAINED_RIGHTS",
    OTHER = "OTHER",
}

export enum ImmigrationStatus {
    /**
    Immigration status.
    ** INDEFINITE_LEAVE_TO_REMAIN ** - Voter has indefinite leave to remain in the UK.
    ** LIMITED_LEAVE_TO_REMAIN ** - Voter has limited leave to remain in the UK.
    ** PRE_SETTLED_STATUS ** - Voter has pre-settled status in the UK.
    ** SETTLED_STATUS ** - Voter has settled status in the UK.
    ** EXEMPT ** - Voter is exempt from immigration status.
    ** NOT_APPLICABLE ** - Voter is not applicable for immigration status.
    */
    INDEFINITE_LEAVE_TO_REMAIN = "INDEFINITE_LEAVE_TO_REMAIN",
    LIMITED_LEAVE_TO_REMAIN = "LIMITED_LEAVE_TO_REMAIN",
    PRE_SETTLED_STATUS = "PRE_SETTLED_STATUS",
    SETTLED_STATUS = "SETTLED_STATUS",
    EXEMPT = "EXEMPT",
    NOT_APPLICABLE = "NOT_APPLICABLE",
}

export enum AddressType {
    /** Current local address (constituency derived from county). */
    LOCAL_CURRENT = "LOCAL_CURRENT",
    /** Past UK address (e.g. before moving overseas). */
    PAST = "PAST",
    /** Non-UK address. */
    OVERSEAS = "OVERSEAS",
}

export enum AddressStatus {
    /**
    Address status (matches backend).
    ** PENDING ** — awaiting verification.
    ** ACTIVE ** — verified / in use.
    ** REJECTED ** — rejected.
    */
    PENDING = "PENDING",
    ACTIVE = "ACTIVE",
    REJECTED = "REJECTED",
}

// Voter model - Represents an organisation in the system
export interface Voter {
    id: string;
    national_insurance_number?: string;
    first_name: string
    surname: string
    previous_first_name?: string
    previous_surname?: string
    date_of_birth: string
    email: string
    voter_reference: string
    constituency_id: string
    nationality_category: NationalityCategory
    immigration_status?: ImmigrationStatus
    immigration_status_expiry?: string
    registration_status: string
    failed_auth_attempts: number
    locked_until?: string
    registered_at?: string
    renew_by?: string
}

// Voter create request model - Represents a request to create a new voter
export interface VoterCreateRequest {
    first_name: string
    surname: string
    previous_first_name?: string
    previous_surname?: string
    date_of_birth: string
    email: string
    national_insurance_number?: string
    passports: Passport[]
    nationality_category: NationalityCategory
    immigration_status?: ImmigrationStatus
    immigration_status_expiry?: string
    renew_by: string
    registration_status: string
}

// Verify identity request model - Represents a request to verify a voter's identity
export interface VerifyIdentityRequest {
    full_name: string
    address_line1: string
    address_line2?: string
    city: string
    postcode: string
}

// Verify identity response model - Represents a response from verifying a voter's identity
export interface VerifyIdentityResponse {
    verified: boolean
    voter_id?: string
    message: string
}

// Voter update request model - Represents a request to update a voter
export interface VoterUpdateRequest {
    first_name?: string
    surname?: string
    previous_first_name?: string
    previous_surname?: string
    date_of_birth?: string
    email?: string
    nationality_category?: NationalityCategory
    immigration_status?: ImmigrationStatus
    immigration_status_expiry?: string
    constituency_id?: string
    renew_by?: string
    registration_status?: string
    failed_auth_attempts?: number
    locked_until?: string
}


// Passport model - Represents a passport entry for a voter
export interface Passport {
    id: string
    passport_number: string
    issuing_country: string
    expiry_date: string
    is_primary: boolean
}

// Create passport request model - Represents a request to create a new passport entry
export interface CreatePassportRequest {
    passport_number: string
    issuing_country: string
    expiry_date?: string
    is_primary: boolean
}

// Update passport request model - Represents a request to update a passport entry
export interface UpdatePassportRequest {
    passport_number?: string
    issuing_country?: string
    expiry_date?: string
    is_primary?: boolean
}

// Passport entry model - Represents a passport entry for a voter
export interface PassportEntry {
    passport_number: string
    issuing_country: string
    expiry_date: string
    is_primary: boolean
}


// Address model - Represents an address for a voter
export interface Address {
    id: string
    address_type?: AddressType
    address_line1: string
    address_line2?: string
    city: string
    postcode: string
    county: string
    country: string
    address_status: AddressStatus
    renew_by?: string
}

// Create address request model - Represents a request to create a new address
export interface CreateAddressRequest {
    address_type: AddressType
    address_line1: string
    address_line2?: string
    city: string
    postcode: string
    county: string
    country: string
    address_status: AddressStatus
    renew_by?: string
}

// Update address request model - Represents a request to update an address
export interface UpdateAddressRequest {
    address_type?: AddressType
    address_line1?: string
    address_line2?: string
    city?: string
    postcode?: string
    county?: string
    country?: string
    address_status?: AddressStatus
    renew_by?: string
}

/** Voter returned from GET/PATCH /voter/{id}, including nested passports. */
export type VoterDetail = Voter & { passports: Passport[] }

export interface VoterLedgerItem {
    id: string
    voter_id: string
    election_id: string
    voted_at?: string
}

export interface CreateVoterLedgerRequest {
    election_id: string
    voted_at?: string
}
