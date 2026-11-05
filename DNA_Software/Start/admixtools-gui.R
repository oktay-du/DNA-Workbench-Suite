.libPaths(c('/opt/dna/R/library',.libPaths()))
options(shiny.host='127.0.0.1',shiny.port=7070,shiny.launch.browser=FALSE)
setwd('/opt/dna/ssd/Projects')
admixtools::run_shiny_admixtools()
