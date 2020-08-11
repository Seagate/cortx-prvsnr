include:
  # TODO EOS-11511 looks like 'require: sls: docker'
  #                doesn't work here (possibly since gitfs is used),
  #                so have to use simple ordering instead of requisites
  - .install_deps
  - .install
