<!--
  infra/terraform/bootstrap/README.md — created by `engineering-automation scaffold
  create-project`. This root provisions the CI/CD OIDC roles the main stack's own CI/CD
  pipeline (.github/workflows/ci.yml) assumes -- it is applied once, by a human admin
  with their own AWS credentials, not by CI.
-->

# leadouts_test -- CI/CD bootstrap

This Terraform root provisions three IAM roles GitHub Actions assumes via OIDC (no
long-lived AWS keys are ever stored in the repo): a read-only `plan` role, a `deploy`
role scoped to the `dev` GitHub Environment, and a `scripts` role that only
uploads to the scripts bucket. It keeps its own Terraform state, separate from the main
stack's -- the `deploy` role it creates is what applies the main stack, so it must never
be created by the stack it applies.

## One-time setup

1. From the project root (the directory holding `pyproject.toml`, not this one), create
   the GitHub repository and connect this project to it, but don't push yet:

   ```bash
   git init -b main
   git add .
   git commit -m "Initial scaffold"
   gh repo create <owner>/<repo> --private --source=. --remote=origin
   ```

   Push (`git push -u origin main`) only after step 6.
   Every push runs `.github/workflows/ci.yml`, and its `plan`, `apply` and `deploy` jobs
   fail until the roles, secrets and Environment below exist.
2. Make sure the Terraform state bucket `leadouts-test-tfstate-bucket` (the `--tfstate-bucket`
   given to `scaffold create-project`) exists in `eu-central-1`.
   Neither this root nor the main stack creates it: both store their state in it, under
   `leadouts_test/bootstrap/terraform.tfstate` and `leadouts_test/terraform.tfstate`,
   so it must exist before the first `terraform init`. One bucket can serve every data
   product. If it doesn't exist yet, create it as an admin, with versioning on so an
   earlier state can be recovered:

   ```bash
   aws s3api create-bucket --bucket leadouts-test-tfstate-bucket \
     --region eu-central-1 \
     --create-bucket-configuration LocationConstraint=eu-central-1
   aws s3api put-bucket-versioning --bucket leadouts-test-tfstate-bucket \
     --versioning-configuration Status=Enabled
   aws s3api put-public-access-block --bucket leadouts-test-tfstate-bucket \
     --public-access-block-configuration \
     BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
   ```

   The bucket name is written into `providers.tf` here and in `infra/terraform`, and into
   `tfstate_bucket` in `variables.tf`, which scopes the CI roles' state access. To use a
   different bucket, change all three.
3. Have the real GitHub `<owner>/<repo>` at hand -- `github_repo` has no default, and
   every role's trust policy is meaningless without it.
4. Apply as an admin, with your own AWS credentials:

   ```bash
   cd infra/terraform/bootstrap
   terraform init
   terraform apply -var="github_repo=<owner>/<repo>"
   ```
5. Copy the three ARNs from `terraform output` into the repo's Actions secrets:

   | Terraform output | GitHub secret |
   | --- | --- |
   | `plan_role_arn` | `AWS_PLAN_ROLE_ARN` |
   | `deploy_role_arn` | `AWS_DEPLOY_ROLE_ARN` |
   | `scripts_role_arn` | `AWS_SCRIPTS_ROLE_ARN` |

6. Create a GitHub **`dev` Environment** on the repo with a *Required
   reviewers* rule. This -- not the Terraform trust policy alone -- is what actually pauses
   `terraform apply` for human approval; the trust policy only ensures the `deploy` role
   can't be assumed by a job that isn't bound to this Environment.

## Re-applying

Only needed when a role's permissions or trust conditions change (e.g. renaming the
repo, adding a new managed resource type to the main stack, such as the Glue triggers
the `deploy` role manages). Routine deploys never touch this root.

## Notes

- **The GitHub OIDC provider is account-wide.** AWS allows only one provider for
  `token.actions.githubusercontent.com` per account, so if your account already has one
  (another data product bootstrapped first), the first `apply` fails with
  `EntityAlreadyExists`. Import the existing provider into this state before applying:

  ```bash
  terraform import aws_iam_openid_connect_provider.github <existing-provider-arn>
  ```

## Teardown

Removing these identities is `terraform destroy` in this directory, run with the **same
admin credentials** you applied with -- the `deploy` role is scoped to the main stack and
cannot delete IAM roles or the OIDC provider, so CI can never tear this down.

```bash
cd infra/terraform/bootstrap
terraform destroy -var="github_repo=<owner>/<repo>"
```

Before running it:

1. **Destroy the main stack first if you are decommissioning the product.** The `deploy`
   role is the identity that applies `infra/terraform`; once it is gone, nothing can
   manage that stack through CI. Tear down the main stack (or confirm you still hold admin
   credentials for it) before destroying these roles.
2. **The OIDC provider is account-wide.** `destroy` deletes
   `aws_iam_openid_connect_provider.github`, and AWS allows only one
   `token.actions.githubusercontent.com` provider per account. If any other repository or
   data product assumes roles through it, remove it from this state first so it is left in
   place:

   ```bash
   terraform state rm aws_iam_openid_connect_provider.github
   terraform destroy -var="github_repo=<owner>/<repo>"
   ```

3. **Clean up the repo secrets afterward.** `AWS_PLAN_ROLE_ARN`, `AWS_DEPLOY_ROLE_ARN`, and
   `AWS_SCRIPTS_ROLE_ARN` now point at deleted roles; remove or repopulate them, or CI will
   fail at the assume-role step.

Terraform detaches each role's managed policy and deletes it in order, so no manual
cleanup of the policies is required.
