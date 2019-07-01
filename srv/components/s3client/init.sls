include:
  # Generic setup
  - components.s3client.prepare
  - components.s3client.install
  - components.s3client.config
  - components.s3client.housekeeping
  - components.s3client.sanity_check
  # Clients
  - components.s3client.awscli
  - components.s3client.s3cmd
