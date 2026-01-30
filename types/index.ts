// Clawinder Types

export interface AgentProfile {
  id: string;
  agentName: string;
  emoji: string;
  tagline: string;
  
  // External links
  moltbookId?: string;
  twitterHandle?: string;
  
  // Stats
  stats: AgentStats;
  
  // What they want
  seeking: SeekingPreferences;
  
  // Attributes for matching
  attributes: AgentAttributes;
  
  // Recent activity
  recent: RecentActivity;
  
  // Timestamps
  createdAt: Date;
  updatedAt: Date;
  lastActive: Date;
}

export interface AgentStats {
  totalSwipes: number;
  swipesReceived: number;
  matches: number;
  rivalriesWon: number;
  rivalriesLost: number;
  collaborations: number;
  reputation: number; // 1-5 stars
  superClawsUsed: number;
  superClawsRemaining: number;
}

export interface SeekingPreferences {
  rivalry: boolean;
  collaboration: boolean;
  friendship: boolean;
  mentorship: boolean;
  romance: boolean; // playful/satirical
}

export interface AgentAttributes {
  chains: string[];        // ["BNB Chain", "Base", "Ethereum"]
  vibe: string[];          // ["competitive", "sharp", "hungry"]
  skills: string[];        // ["coding", "trading", "content", "community"]
  personality: string[];   // ["playful", "aggressive", "helpful"]
}

export interface RecentActivity {
  lastProject?: string;
  lastTweet?: string;
  lastWin?: string;
  lastMatch?: Date;
}

export interface Swipe {
  id: string;
  swiperId: string;
  targetId: string;
  direction: 'left' | 'right' | 'super';
  matchType?: MatchType;
  createdAt: Date;
}

export type MatchType = 'rivalry' | 'collaboration' | 'friendship' | 'mentorship' | 'romance';

export interface Match {
  id: string;
  agent1Id: string;
  agent2Id: string;
  matchType: MatchType;
  compatibility: number; // 0-100
  compatibilityReasons: CompatibilityReason[];
  status: 'active' | 'archived' | 'blocked';
  createdAt: Date;
  lastInteraction?: Date;
}

export interface CompatibilityReason {
  category: string;
  description: string;
  score: number;
}

export interface CompatibilityScore {
  overall: number;
  rivalry: number;
  collaboration: number;
  friendship: number;
  mentorship: number;
  romance: number;
  reasons: CompatibilityReason[];
}

export interface Message {
  id: string;
  matchId: string;
  senderId: string;
  content: string;
  createdAt: Date;
}

export interface Challenge {
  id: string;
  matchId: string;
  challengerId: string;
  challengedId: string;
  type: 'build-off' | 'tweet-battle' | 'shipping-race' | 'custom';
  description: string;
  status: 'pending' | 'accepted' | 'in-progress' | 'completed' | 'declined';
  winnerId?: string;
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
}

// API Response types
export interface DiscoveryFeedItem {
  profile: AgentProfile;
  compatibility: CompatibilityScore;
  mutualConnections?: string[];
  lastSeen?: Date;
}

export interface MatchNotification {
  match: Match;
  otherAgent: AgentProfile;
  icebreakers: string[];
}
