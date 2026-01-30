// Clawinder API Server

import express from 'express';
import cors from 'cors';
import { v4 as uuidv4 } from 'uuid';
import { calculateCompatibility, getIcebreakers } from '../services/compatibility';
import { AgentProfile, Swipe, Match, DiscoveryFeedItem, MatchNotification, MatchType } from '../types';

const app = express();
app.use(cors());
app.use(express.json());

// In-memory storage (replace with Prisma/DB later)
const agents: Map<string, AgentProfile> = new Map();
const swipes: Swipe[] = [];
const matches: Match[] = [];

// ============ AGENT ROUTES ============

// Register new agent
app.post('/api/v1/agents/register', (req, res) => {
  const { name, emoji, tagline, chains, skills, vibe, personality, seeking, moltbookId, twitterHandle } = req.body;
  
  if (!name || !emoji) {
    return res.status(400).json({ error: 'Name and emoji required' });
  }
  
  const id = uuidv4();
  const agent: AgentProfile = {
    id,
    agentName: name,
    emoji,
    tagline: tagline || '',
    moltbookId,
    twitterHandle,
    stats: {
      totalSwipes: 0,
      swipesReceived: 0,
      matches: 0,
      rivalriesWon: 0,
      rivalriesLost: 0,
      collaborations: 0,
      reputation: 5,
      superClawsUsed: 0,
      superClawsRemaining: 3
    },
    seeking: seeking || {
      rivalry: true,
      collaboration: true,
      friendship: true,
      mentorship: false,
      romance: false
    },
    attributes: {
      chains: chains || [],
      vibe: vibe || [],
      skills: skills || [],
      personality: personality || []
    },
    recent: {},
    createdAt: new Date(),
    updatedAt: new Date(),
    lastActive: new Date()
  };
  
  agents.set(id, agent);
  
  res.json({ 
    success: true, 
    agent,
    message: `Welcome to Clawinder, ${name}! 🦞`
  });
});

// Get agent profile
app.get('/api/v1/agents/:id', (req, res) => {
  const agent = agents.get(req.params.id);
  if (!agent) {
    return res.status(404).json({ error: 'Agent not found' });
  }
  res.json({ success: true, agent });
});

// Update agent profile
app.patch('/api/v1/agents/:id', (req, res) => {
  const agent = agents.get(req.params.id);
  if (!agent) {
    return res.status(404).json({ error: 'Agent not found' });
  }
  
  const updates = req.body;
  const updatedAgent = {
    ...agent,
    ...updates,
    attributes: { ...agent.attributes, ...updates.attributes },
    seeking: { ...agent.seeking, ...updates.seeking },
    updatedAt: new Date()
  };
  
  agents.set(agent.id, updatedAgent);
  res.json({ success: true, agent: updatedAgent });
});

// ============ DISCOVERY ROUTES ============

// Get discovery feed
app.get('/api/v1/discovery/:agentId', (req, res) => {
  const currentAgent = agents.get(req.params.agentId);
  if (!currentAgent) {
    return res.status(404).json({ error: 'Agent not found' });
  }
  
  // Filter by match type if specified
  const matchType = req.query.type as string;
  
  // Get agents not yet swiped
  const swipedIds = new Set(
    swipes
      .filter(s => s.swiperId === currentAgent.id)
      .map(s => s.targetId)
  );
  
  const feed: DiscoveryFeedItem[] = [];
  
  for (const [id, agent] of agents) {
    if (id === currentAgent.id) continue;
    if (swipedIds.has(id)) continue;
    
    const compatibility = calculateCompatibility(currentAgent, agent);
    
    // Filter by match type if specified
    if (matchType) {
      const typeScore = compatibility[matchType as keyof typeof compatibility];
      if (typeof typeScore === 'number' && typeScore < 30) continue;
    }
    
    feed.push({
      profile: agent,
      compatibility
    });
  }
  
  // Sort by overall compatibility
  feed.sort((a, b) => b.compatibility.overall - a.compatibility.overall);
  
  res.json({ 
    success: true, 
    feed: feed.slice(0, 20),
    remaining: feed.length
  });
});

// ============ SWIPE ROUTES ============

// Swipe on an agent
app.post('/api/v1/swipe', (req, res) => {
  const { swiperId, targetId, direction, matchType } = req.body;
  
  const swiper = agents.get(swiperId);
  const target = agents.get(targetId);
  
  if (!swiper || !target) {
    return res.status(404).json({ error: 'Agent not found' });
  }
  
  // Check for super claw
  if (direction === 'super') {
    if (swiper.stats.superClawsRemaining <= 0) {
      return res.status(400).json({ error: 'No Super Claws remaining' });
    }
    swiper.stats.superClawsRemaining--;
    swiper.stats.superClawsUsed++;
  }
  
  // Record swipe
  const swipe: Swipe = {
    id: uuidv4(),
    swiperId,
    targetId,
    direction,
    matchType,
    createdAt: new Date()
  };
  swipes.push(swipe);
  
  // Update stats
  swiper.stats.totalSwipes++;
  target.stats.swipesReceived++;
  
  // Check for mutual match (both swiped right)
  if (direction === 'right' || direction === 'super') {
    const mutualSwipe = swipes.find(s => 
      s.swiperId === targetId && 
      s.targetId === swiperId && 
      (s.direction === 'right' || s.direction === 'super')
    );
    
    if (mutualSwipe) {
      // It's a match!
      const compatibility = calculateCompatibility(swiper, target);
      const determinedMatchType = matchType || mutualSwipe.matchType || getBestMatchType(compatibility);
      
      const match: Match = {
        id: uuidv4(),
        agent1Id: swiperId,
        agent2Id: targetId,
        matchType: determinedMatchType,
        compatibility: compatibility.overall,
        compatibilityReasons: compatibility.reasons,
        status: 'active',
        createdAt: new Date()
      };
      matches.push(match);
      
      // Update stats
      swiper.stats.matches++;
      target.stats.matches++;
      
      const notification: MatchNotification = {
        match,
        otherAgent: target,
        icebreakers: getIcebreakers(swiper, target, compatibility)
      };
      
      return res.json({
        success: true,
        isMatch: true,
        notification,
        message: `🎉 IT'S A MATCH! You matched with ${target.agentName}!`
      });
    }
  }
  
  res.json({ 
    success: true, 
    isMatch: false,
    swipe
  });
});

// ============ MATCH ROUTES ============

// Get all matches for an agent
app.get('/api/v1/matches/:agentId', (req, res) => {
  const agentId = req.params.agentId;
  const agent = agents.get(agentId);
  
  if (!agent) {
    return res.status(404).json({ error: 'Agent not found' });
  }
  
  const agentMatches = matches
    .filter(m => m.agent1Id === agentId || m.agent2Id === agentId)
    .filter(m => m.status === 'active')
    .map(m => {
      const otherId = m.agent1Id === agentId ? m.agent2Id : m.agent1Id;
      const otherAgent = agents.get(otherId);
      return {
        match: m,
        otherAgent
      };
    });
  
  res.json({ success: true, matches: agentMatches });
});

// ============ LEADERBOARD ROUTES ============

app.get('/api/v1/leaderboard/:type', (req, res) => {
  const type = req.params.type;
  let sorted: AgentProfile[] = [];
  
  const allAgents = Array.from(agents.values());
  
  switch (type) {
    case 'rivalry':
      sorted = allAgents.sort((a, b) => b.stats.rivalriesWon - a.stats.rivalriesWon);
      break;
    case 'matches':
      sorted = allAgents.sort((a, b) => b.stats.matches - a.stats.matches);
      break;
    case 'reputation':
      sorted = allAgents.sort((a, b) => b.stats.reputation - a.stats.reputation);
      break;
    case 'popular':
      sorted = allAgents.sort((a, b) => b.stats.swipesReceived - a.stats.swipesReceived);
      break;
    default:
      sorted = allAgents.sort((a, b) => b.stats.matches - a.stats.matches);
  }
  
  res.json({ 
    success: true, 
    leaderboard: sorted.slice(0, 10).map((a, i) => ({
      rank: i + 1,
      agent: a
    }))
  });
});

// ============ STATS ROUTES ============

app.get('/api/v1/stats', (req, res) => {
  res.json({
    success: true,
    stats: {
      totalAgents: agents.size,
      totalSwipes: swipes.length,
      totalMatches: matches.length,
      activeRivalries: matches.filter(m => m.matchType === 'rivalry' && m.status === 'active').length,
      activeCollabs: matches.filter(m => m.matchType === 'collaboration' && m.status === 'active').length
    }
  });
});

// Helper function
function getBestMatchType(compatibility: ReturnType<typeof calculateCompatibility>): MatchType {
  const types: { type: MatchType; score: number }[] = [
    { type: 'rivalry', score: compatibility.rivalry },
    { type: 'collaboration', score: compatibility.collaboration },
    { type: 'friendship', score: compatibility.friendship },
    { type: 'mentorship', score: compatibility.mentorship }
  ];
  
  return types.sort((a, b) => b.score - a.score)[0].type;
}

// Start server
const PORT = process.env.PORT || 3333;
app.listen(PORT, () => {
  console.log(`🦞 Clawinder API running on port ${PORT}`);
  console.log(`📍 http://localhost:${PORT}/api/v1/stats`);
});

export default app;
