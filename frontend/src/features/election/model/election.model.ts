// election.model.ts - Election model

export enum ElectionType {
  GENERAL = "GENERAL",
  LOCAL = "LOCAL",
  SCOTTISH_PARLIAMENT = "SCOTTISH_PARLIAMENT",
  NORTHERN_IRELAND_ASSEMBLY = "NORTHERN_IRELAND_ASSEMBLY",
  WELSH_PARLIAMENT = "WELSH_PARLIAMENT",
  MAYORS = "MAYORS",
  POLICE_AND_CRIME_COMMISSIONER = "POLICE_AND_CRIME_COMMISSIONER",
}

export enum ElectionScope {
  NATIONAL = "NATIONAL",
  REGIONAL = "REGIONAL",
  LOCAL = "LOCAL",
}

export enum ElectionStatus {
  OPEN = "OPEN",
  CLOSED = "CLOSED",
}

export interface Election {
  id: string;
  title: string;
  election_type: ElectionType;
  scope: ElectionScope;
  allocation_method: string;
  status: ElectionStatus;
  voting_opens?: string;
  voting_closes?: string;
  created_by?: string;
}

export interface CreateElectionRequest {
  title: string;
  election_type: ElectionType;
  scope: ElectionScope;
  allocation_method: string;
  status: ElectionStatus;
  voting_opens?: string;
  voting_closes?: string;
  created_by?: string;
}

export interface UpdateElectionRequest {
  status?: ElectionStatus;
  voting_opens?: string;
  voting_closes?: string;
}
