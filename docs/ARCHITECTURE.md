# Phase-1 Architecture

```text
Browser
  |
  v
React + MapLibre
  |
  +--> Cognito authentication
  |
  v
FastAPI
  |
  +--> Intent normalization boundary
  +--> Project/story-point API
  +--> Geocoder adapter ------> Amazon Location Places
  +--> Export boundary -------> static/preview renderer
  |
  +--> PostgreSQL/PostGIS
  +--> S3 artifacts
```

## Why this is intentionally not a large agentic architecture

The application is dominated by deterministic state and geography. AI is useful at the intent boundary, but coordinates, persistence, auth, and export correctness are ordinary software concerns.

## Core bounded concepts

### LocationStoryProject
Ownership, intent, viewport, style, version.

### StoryPoint
A verified/manual coordinate plus presentation metadata.

### LocationStoryIntent
The structured interpretation of what the user wants to communicate.

### Artifact
A versioned output generated from a validated project snapshot.

## Future extension points

- commercial POI providers
- demographic/labor datasets
- location-scoring recipes
- billing/chargeback
- branded template libraries
- high-resolution renderer
- PowerPoint/PDF generation
- enterprise tenant administration
