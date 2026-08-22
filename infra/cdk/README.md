# CDK implementation intent

Use AWS CDK in TypeScript.

Create stacks by concern only if justified:
1. `IdentityStack`
2. `DataStack`
3. `ApplicationStack`

Do not create a large platform abstraction for Phase 1.
Export only the minimum cross-stack values required.
