// election.model.ts - Election model

export enum ElectionType {
  // FPTP elections
  GENERAL = "GENERAL",
  LOCAL_ENGLAND_WALES = "LOCAL_ENGLAND_WALES",
  MAYORS = "MAYORS",
  POLICE_AND_CRIME_COMMISSIONER = "POLICE_AND_CRIME_COMMISSIONER",
  SCOTTISH_NATIONAL_PARK = "SCOTTISH_NATIONAL_PARK",

  // AMS elections
  SCOTTISH_PARLIAMENT = "SCOTTISH_PARLIAMENT",
  LONDON_ASSEMBLY = "LONDON_ASSEMBLY",

  // STV elections
  NORTHERN_IRELAND_ASSEMBLY = "NORTHERN_IRELAND_ASSEMBLY",
  LOCAL_NORTHERN_IRELAND_SCOTLAND = "LOCAL_NORTHERN_IRELAND_SCOTLAND",

  // Alternative Vote elections
  HOUSE_OF_LORDS_HEREDITARY = "HOUSE_OF_LORDS_HEREDITARY",
  SCOTTISH_CROFTING_COMMISSION = "SCOTTISH_CROFTING_COMMISSION",
}

export enum AllocationMethod {
  FPTP = "FPTP",
  AMS = "AMS",
  STV = "STV",
  ALTERNATIVE_VOTE = "ALTERNATIVE_VOTE",
}

/** Maps each election type to its electoral system. */
export const ELECTION_TYPE_ALLOCATION_MAP: Record<ElectionType, AllocationMethod> = {
  [ElectionType.GENERAL]: AllocationMethod.FPTP,
  [ElectionType.LOCAL_ENGLAND_WALES]: AllocationMethod.FPTP,
  [ElectionType.MAYORS]: AllocationMethod.FPTP,
  [ElectionType.POLICE_AND_CRIME_COMMISSIONER]: AllocationMethod.FPTP,
  [ElectionType.SCOTTISH_NATIONAL_PARK]: AllocationMethod.FPTP,
  [ElectionType.SCOTTISH_PARLIAMENT]: AllocationMethod.AMS,
  [ElectionType.LONDON_ASSEMBLY]: AllocationMethod.AMS,
  [ElectionType.NORTHERN_IRELAND_ASSEMBLY]: AllocationMethod.STV,
  [ElectionType.LOCAL_NORTHERN_IRELAND_SCOTLAND]: AllocationMethod.STV,
  [ElectionType.HOUSE_OF_LORDS_HEREDITARY]: AllocationMethod.ALTERNATIVE_VOTE,
  [ElectionType.SCOTTISH_CROFTING_COMMISSION]: AllocationMethod.ALTERNATIVE_VOTE,
};

/** Human-readable labels for election types. */
export const ELECTION_TYPE_LABELS: Record<ElectionType, string> = {
  [ElectionType.GENERAL]: "General Election (House of Commons)",
  [ElectionType.LOCAL_ENGLAND_WALES]: "Local Council Election (England & Wales)",
  [ElectionType.MAYORS]: "Mayoral Election (England)",
  [ElectionType.POLICE_AND_CRIME_COMMISSIONER]: "Police and Crime Commissioner",
  [ElectionType.SCOTTISH_NATIONAL_PARK]: "Scottish National Park Authority",
  [ElectionType.SCOTTISH_PARLIAMENT]: "Scottish Parliament",
  [ElectionType.LONDON_ASSEMBLY]: "London Assembly",
  [ElectionType.NORTHERN_IRELAND_ASSEMBLY]: "Northern Ireland Assembly",
  [ElectionType.LOCAL_NORTHERN_IRELAND_SCOTLAND]: "Local Council Election (NI & Scotland)",
  [ElectionType.HOUSE_OF_LORDS_HEREDITARY]: "House of Lords (Hereditary Peers)",
  [ElectionType.SCOTTISH_CROFTING_COMMISSION]: "Scottish Crofting Commission",
};

/** Human-readable labels for allocation methods. */
export const ALLOCATION_METHOD_LABELS: Record<AllocationMethod, string> = {
  [AllocationMethod.FPTP]: "First Past The Post (FPTP)",
  [AllocationMethod.AMS]: "Additional Member System (AMS)",
  [AllocationMethod.STV]: "Single Transferable Vote (STV)",
  [AllocationMethod.ALTERNATIVE_VOTE]: "Alternative Vote (AV)",
};

export enum ElectionScope {
  NATIONAL = "NATIONAL",
  REGIONAL = "REGIONAL",
  LOCAL = "LOCAL",
}

export enum ElectionStatus {
  OPEN = "OPEN",
  CLOSED = "CLOSED",
  CANCELLED = "CANCELLED",
}

export interface Election {
  id: string;
  title: string;
  election_type: ElectionType;
  scope: ElectionScope;
  allocation_method: AllocationMethod;
  status: ElectionStatus;
  voting_opens?: string;
  voting_closes?: string;
  created_by?: string;
}

export interface CreateElectionRequest {
  title: string;
  election_type: ElectionType;
  scope: ElectionScope;
  voting_opens?: string;
  voting_closes?: string;
  created_by?: string;
}

export interface UpdateElectionRequest {
  status?: ElectionStatus;
  voting_opens?: string;
  voting_closes?: string;
}
