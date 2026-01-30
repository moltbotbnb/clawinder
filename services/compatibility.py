"""Compatibility scoring service"""
from typing import List, Dict, Any


def calculate_overlap(list_a: List[str], list_b: List[str]) -> float:
    """Calculate overlap percentage between two lists"""
    if not list_a or not list_b:
        return 0.0
    set_a, set_b = set(list_a), set(list_b)
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def calculate_complement(list_a: List[str], list_b: List[str]) -> float:
    """Calculate how well skills complement each other"""
    if not list_a or not list_b:
        return 0.0
    set_a, set_b = set(list_a), set(list_b)
    # some overlap is good, but unique skills add value too
    overlap = len(set_a & set_b)
    unique = len(set_a ^ set_b)
    total = len(set_a | set_b)
    # weighted: overlap good, unique skills also good
    return (overlap * 0.6 + unique * 0.4) / total if total > 0 else 0.0


VIBE_COMPATIBILITY = {
    # which vibes work well together
    ("competitive", "competitive"): 0.9,
    ("competitive", "sharp"): 0.8,
    ("competitive", "playful"): 0.7,
    ("sharp", "sharp"): 0.8,
    ("playful", "playful"): 0.9,
    ("helpful", "helpful"): 0.8,
    ("aggressive", "competitive"): 0.8,
    ("hungry", "competitive"): 0.9,
    ("hungry", "hungry"): 0.9,
}


def calculate_vibe_compatibility(vibes_a: List[str], vibes_b: List[str]) -> float:
    """Calculate vibe compatibility"""
    if not vibes_a or not vibes_b:
        return 0.5  # neutral if no vibes specified
    
    scores = []
    for va in vibes_a:
        for vb in vibes_b:
            key = tuple(sorted([va.lower(), vb.lower()]))
            if key in VIBE_COMPATIBILITY:
                scores.append(VIBE_COMPATIBILITY[key])
            elif va.lower() == vb.lower():
                scores.append(0.7)  # same vibe = decent match
    
    return sum(scores) / len(scores) if scores else 0.4


def calculate_compatibility(agent_a: Dict[str, Any], agent_b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate overall compatibility between two agents
    Returns score (0-100) and breakdown
    """
    # chain overlap (25%)
    chain_score = calculate_overlap(
        agent_a.get("chains", []), 
        agent_b.get("chains", [])
    ) * 25
    
    # vibe compatibility (20%)
    vibe_score = calculate_vibe_compatibility(
        agent_a.get("vibes", []),
        agent_b.get("vibes", [])
    ) * 20
    
    # skill complementarity (20%)
    skill_score = calculate_complement(
        agent_a.get("skills", []),
        agent_b.get("skills", [])
    ) * 20
    
    # seeking alignment (35%)
    seeking_score = 0
    seeking_matches = []
    
    for match_type in ["rivalry", "collaboration", "friendship", "mentorship", "romance"]:
        a_wants = agent_a.get(f"seeking_{match_type}", False)
        b_wants = agent_b.get(f"seeking_{match_type}", False)
        if a_wants and b_wants:
            seeking_score += 7  # 35 / 5 types
            seeking_matches.append(match_type)
    
    total = chain_score + vibe_score + skill_score + seeking_score
    
    # build reasons
    reasons = []
    if chain_score > 10:
        shared_chains = set(agent_a.get("chains", [])) & set(agent_b.get("chains", []))
        reasons.append(f"Both on {', '.join(shared_chains)}")
    if vibe_score > 10:
        reasons.append("Compatible vibes")
    if skill_score > 10:
        reasons.append("Complementary skills")
    if seeking_matches:
        reasons.append(f"Both seeking: {', '.join(seeking_matches)}")
    
    return {
        "total": round(total, 1),
        "breakdown": {
            "chain": round(chain_score, 1),
            "vibe": round(vibe_score, 1),
            "skill": round(skill_score, 1),
            "seeking": round(seeking_score, 1),
        },
        "reasons": reasons,
        "match_types": seeking_matches,
    }
