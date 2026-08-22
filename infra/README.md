# AWS Infrastructure Scaffold

Phase-1 intended resources:

- CloudFront + private S3 frontend bucket
- Cognito User Pool + App Client
- ALB + ECS Fargate FastAPI service
- RDS PostgreSQL/PostGIS
- private S3 artifact bucket
- Amazon Location Service access
- CloudWatch logs
- Secrets Manager references
- least-privilege IAM roles

This starter intentionally leaves exact account/VPC conventions unresolved because enterprise network standards vary. Implement these only after inspecting the target AWS landing-zone conventions.

## Required deployment inputs

- AWS account/region
- VPC/subnet strategy
- DNS/domain
- certificate
- Cognito federation requirements
- database sizing/backups
- artifact retention policy
- Amazon Location authorization method
