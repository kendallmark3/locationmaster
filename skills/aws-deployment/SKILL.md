# Skill — AWS Deployment

## Purpose
Keep deployment choices narrow and repeatable.

## Phase-1 target
- React static frontend: S3 + CloudFront
- FastAPI: ECS Fargate behind ALB (or approved equivalent)
- Auth: Cognito
- Database: RDS PostgreSQL with PostGIS
- Artifacts: S3
- Maps/geocoding: Amazon Location Service
- Secrets: AWS Secrets Manager / task environment references
- Logs: CloudWatch

## Rules
- No secrets in repo.
- Separate dev/stage/prod parameters.
- Least-privilege IAM.
- S3 buckets private by default.
- Database not publicly reachable.
