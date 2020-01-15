Sync data:
  module.run:
    - saltutil.clear_cache: []
    - saltutil.sync_all: []
    - saltutil.refresh_grains: []
    - saltutil.refresh_modules: []
    - saltutil.refresh_pillar: []
    - mine.update: []

include:
  - components.system.prepare.setup_yum_repos
