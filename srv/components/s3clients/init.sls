include:
  # Generic setup
  - components.s3clients.prepare
  - components.s3clients.install
  - components.s3clients.config
  - components.s3clients.housekeeping
  - components.s3clients.sanity_check
  # Clients
  - components.s3clients.awscli
  - components.s3clients.s3cmd
