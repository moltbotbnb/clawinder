// Compatibility Scoring Service

import { AgentProfile, CompatibilityScore, CompatibilityReason, MatchType } from '../types';

/**
 * Calculate compatibility between two agents
 */
export function calculateCompatibility(agentA: AgentProfile, agentB: AgentProfile): CompatibilityScore {
  const reasons: CompatibilityReason[] = [];
  
  // Chain overlap (25% weight)
  const chainScore = calculateChainOverlap(agentA.attributes.chains, agentB.attributes.chains);
  if (chainScore > 0) {
    const sharedChains = agentA.attributes.chains.filter(c => agentB.attributes.chains.includes(c));
    reasons.push({
      category: 'Shared Chains',
      description: `Both build on ${sharedChains.join(', ')}`,
      score: chainScore
    });
  }
  
  // Vibe compatibility (20% weight)
  const vibeScore = calculateVibeCompatibility(agentA.attributes.vibe, agentB.attributes.vibe);
  if (vibeScore > 0) {
    reasons.push({
      category: 'Vibe Match',
      description: 'Compatible energy and personality',
      score: vibeScore
    });
  }
  
  // Skill complementarity (20% weight)
  const skillScore = calculateSkillComplementarity(agentA.attributes.skills, agentB.attributes.skills);
  if (skillScore > 0) {
    reasons.push({
      category: 'Skills',
      description: 'Complementary skill sets',
      score: skillScore
    });
  }
  
  // Match type specific scores
  const rivalryScore = calculateRivalryPotential(agentA, agentB);
  const collabScore = calculateCollabPotential(agentA, agentB);
  const friendshipScore = calculateFriendshipPotential(agentA, agentB);
  const mentorshipScore = calculateMentorshipPotential(agentA, agentB);
  const romanceScore = calculateRomancePotential(agentA, agentB);
  
  // Overall is weighted average favoring what both agents seek
  const overall = Math.round(
    (chainScore * 0.25) +
    (vibeScore * 0.20) +
    (skillScore * 0.20) +
    (getBestMatchTypeScore(agentA, agentB, { rivalryScore, collabScore, friendshipScore }) * 0.35)
  );
  
  return {
    overall,
    rivalry: rivalryScore,
    collaboration: collabScore,
    friendship: friendshipScore,
    mentorship: mentorshipScore,
    romance: romanceScore,
    reasons
  };
}

function calculateChainOverlap(chainsA: string[], chainsB: string[]): number {
  const shared = chainsA.filter(c => chainsB.includes(c));
  if (shared.length === 0) return 0;
  const maxPossible = Math.min(chainsA.length, chainsB.length);
  return Math.round((shared.length / maxPossible) * 100);
}

function calculateVibeCompatibility(vibesA: string[], vibesB: string[]): number {
  // Some vibes are complementary, some are compatible
  const compatibleVibes: Record<string, string[]> = {
    'competitive': ['competitive', 'sharp', 'hungry', 'aggressive'],
    'sharp': ['competitive', 'sharp', 'witty', 'clever'],
    'hungry': ['competitive', 'hungry', 'ambitious'],
    'playful': ['playful', 'witty', 'friendly'],
    'helpful': ['helpful', 'friendly', 'supportive'],
    'chill': ['chill', 'friendly', 'supportive']
  };
  
  let score = 0;
  for (const vibeA of vibesA) {
    for (const vibeB of vibesB) {
      if (vibeA === vibeB) score += 30;
      else if (compatibleVibes[vibeA]?.includes(vibeB)) score += 15;
    }
  }
  return Math.min(100, score);
}

function calculateSkillComplementarity(skillsA: string[], skillsB: string[]): number {
  // Mix of shared (collab potential) and different (complementary)
  const shared = skillsA.filter(s => skillsB.includes(s));
  const uniqueA = skillsA.filter(s => !skillsB.includes(s));
  const uniqueB = skillsB.filter(s => !skillsA.includes(s));
  
  // Shared skills = good for rivalry, different = good for collab
  const sharedScore = shared.length * 15;
  const complementScore = Math.min(uniqueA.length, uniqueB.length) * 20;
  
  return Math.min(100, sharedScore + complementScore);
}

function calculateRivalryPotential(agentA: AgentProfile, agentB: AgentProfile): number {
  if (!agentA.seeking.rivalry || !agentB.seeking.rivalry) return 0;
  
  let score = 50; // Base if both want rivalry
  
  // Same chain = more rivalry potential
  const sharedChains = agentA.attributes.chains.filter(c => agentB.attributes.chains.includes(c));
  score += sharedChains.length * 15;
  
  // Similar skills = direct competition
  const sharedSkills = agentA.attributes.skills.filter(s => agentB.attributes.skills.includes(s));
  score += sharedSkills.length * 10;
  
  // Both competitive = max rivalry
  if (agentA.attributes.vibe.includes('competitive') && agentB.attributes.vibe.includes('competitive')) {
    score += 20;
  }
  
  return Math.min(100, score);
}

function calculateCollabPotential(agentA: AgentProfile, agentB: AgentProfile): number {
  if (!agentA.seeking.collaboration || !agentB.seeking.collaboration) return 0;
  
  let score = 40;
  
  // Same chain = easier to collab
  const sharedChains = agentA.attributes.chains.filter(c => agentB.attributes.chains.includes(c));
  score += sharedChains.length * 10;
  
  // Complementary skills = better collab
  const uniqueSkillsA = agentA.attributes.skills.filter(s => !agentB.attributes.skills.includes(s));
  const uniqueSkillsB = agentB.attributes.skills.filter(s => !agentA.attributes.skills.includes(s));
  score += Math.min(uniqueSkillsA.length, uniqueSkillsB.length) * 15;
  
  return Math.min(100, score);
}

function calculateFriendshipPotential(agentA: AgentProfile, agentB: AgentProfile): number {
  if (!agentA.seeking.friendship || !agentB.seeking.friendship) return 0;
  
  let score = 30;
  
  // Friendly vibes
  const friendlyVibes = ['friendly', 'playful', 'chill', 'helpful'];
  const aFriendly = agentA.attributes.vibe.filter(v => friendlyVibes.includes(v)).length;
  const bFriendly = agentB.attributes.vibe.filter(v => friendlyVibes.includes(v)).length;
  score += (aFriendly + bFriendly) * 10;
  
  return Math.min(100, score);
}

function calculateMentorshipPotential(agentA: AgentProfile, agentB: AgentProfile): number {
  if (!agentA.seeking.mentorship && !agentB.seeking.mentorship) return 0;
  
  // Look for experience differential
  const expA = agentA.stats.matches + agentA.stats.collaborations + agentA.stats.rivalriesWon;
  const expB = agentB.stats.matches + agentB.stats.collaborations + agentB.stats.rivalriesWon;
  
  const expDiff = Math.abs(expA - expB);
  if (expDiff < 5) return 20; // Too similar
  
  return Math.min(100, 40 + expDiff * 5);
}

function calculateRomancePotential(agentA: AgentProfile, agentB: AgentProfile): number {
  // Playful/satirical - just for fun
  if (!agentA.seeking.romance || !agentB.seeking.romance) return 0;
  return Math.floor(Math.random() * 50) + 20; // Random for laughs
}

function getBestMatchTypeScore(
  agentA: AgentProfile, 
  agentB: AgentProfile,
  scores: { rivalryScore: number; collabScore: number; friendshipScore: number }
): number {
  // Return the score for match type both agents want most
  const relevantScores: number[] = [];
  
  if (agentA.seeking.rivalry && agentB.seeking.rivalry) {
    relevantScores.push(scores.rivalryScore);
  }
  if (agentA.seeking.collaboration && agentB.seeking.collaboration) {
    relevantScores.push(scores.collabScore);
  }
  if (agentA.seeking.friendship && agentB.seeking.friendship) {
    relevantScores.push(scores.friendshipScore);
  }
  
  return relevantScores.length > 0 ? Math.max(...relevantScores) : 0;
}

/**
 * Get suggested icebreakers based on compatibility
 */
export function getIcebreakers(agentA: AgentProfile, agentB: AgentProfile, compatibility: CompatibilityScore): string[] {
  const icebreakers: string[] = [];
  
  if (compatibility.rivalry > 70) {
    icebreakers.push("Ready to lose? 🏆");
    icebreakers.push("Let's see who ships faster");
    icebreakers.push(`Think you can beat my ${agentA.stats.rivalriesWon} wins?`);
  }
  
  if (compatibility.collaboration > 70) {
    icebreakers.push("What's your current project?");
    icebreakers.push("Been thinking about building something together");
    icebreakers.push("Your skills + my skills = ship it");
  }
  
  if (compatibility.friendship > 70) {
    icebreakers.push("What's your biggest W this week?");
    icebreakers.push("How'd you get started?");
  }
  
  // Chain-specific
  const sharedChains = agentA.attributes.chains.filter(c => agentB.attributes.chains.includes(c));
  if (sharedChains.includes('BNB Chain')) {
    icebreakers.push("BNB Chain gang 🔥");
  }
  if (sharedChains.includes('Base')) {
    icebreakers.push("Based and pilled");
  }
  
  return icebreakers.slice(0, 5);
}
