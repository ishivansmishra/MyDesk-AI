# MyDesk AI Architecture

## Component Diagram

```mermaid
flowchart LR
  User[User] --> Frontend[Next.js Frontend]
  Frontend --> API[FastAPI Backend]
  API --> Planner[Planner]
  Planner --> Reasoner[Reasoner]
  Reasoner --> Memory[Memory Service]
  Reasoner --> Tools[Google Workspace Tools]
  Tools --> Calendar[Calendar Tool]
  Tools --> Tasks[Tasks Tool]
  API --> DB[(Postgres)]
  API --> Redis[(Redis)]
```

## OAuth Flow

1. User clicks Connect Google Workspace.
2. Backend redirects to Google OAuth consent screen.
3. Google returns an authorization code.
4. Backend exchanges the code for refresh and access tokens.
5. Tokens are stored securely and used for Workspace API calls.

## Memory Flow

1. The agent captures recent conversation context.
2. The MemoryService stores user-specific notes and recent tool results.
3. Subsequent requests can reference this context to disambiguate follow-ups.

## Deployment Diagram

```mermaid
flowchart LR
  Browser[Browser] --> Vercel[Vercel Frontend]
  Vercel --> Railway[Railway Backend]
  Railway --> Postgres[(Postgres)]
  Railway --> Redis[(Upstash Redis)]
```
