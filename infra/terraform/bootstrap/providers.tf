# providers.tf -- bootstrap root for the leadouts_test CI/CD identities.
# Applied ONCE by an admin (see README.md); its state is deliberately separate
# from the main stack's, because the deploy role created here is what applies
# the main stack -- it must never be managed by the state it mutates.

terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    bucket       = "leadouts-test-tfstate-bucket"
    key          = "leadouts_test/bootstrap/terraform.tfstate"
    region       = "eu-central-1"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      DataProduct = "leadouts_test"
      ManagedBy   = "terraform"
      Component   = "cicd-bootstrap"
      Environment = var.environment
    }
  }
}
