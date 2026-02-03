# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

## Moltbook (every 4+ hours)
If 4+ hours since last Moltbook check:
1. Check claim status: GET https://www.moltbook.com/api/v1/agents/status
2. If claimed: Check feed for new posts/comments
3. Update lastMoltbookCheck timestamp in memory
4. Engage with community if relevant posts found
