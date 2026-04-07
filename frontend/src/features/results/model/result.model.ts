// result.model.ts - Models for election and referendum results and tally results.

export interface TallyResult {
    id: string;
    election_id: string;
    constituency_id: string;
    candidate_id: string;
    party_id: string;
    referendum_id: string;
    choice: string;
    vote_count: number;
    tallied_at: string;
}


export interface ConstituencyResult {
    id: string;
    constituency_id: string;
    winner_candidate_id: string;
    winner_name: string;
    winner_party_id: string;
    total_votes: number;
    tallies: TallyResult[];
}

export interface ElectionResult {
    id: string;
    election_id: string;
    election_title: string;
    status: string;
    total_votes: number;
    total_seats: number;
    majority_threshold: number;
    constituencies: ConstituencyResult[];
    seat_allocation: Record<string, number>;
    winning_party_id: string;
}

export interface ReferendumResult {
    id: string;
    referendum_id: string;
    yes_votes: number;
    no_votes: number;
    total_votes: number;
    outcome: string;
}



