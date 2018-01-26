# PF Covariate Generation

This repository contains a python-based reimplementation of the code described in
"Re-examining environmental correlates of *Plasmodium falciparum* malaria endemicity:
a data-intensive variable selection approach" (Weiss et al, 2015,
doi: 10.1186/s12936-015-0574-x)

Briefly, this study took various temporally-dynamic "cubes" of raster covariates based on MODIS
data (held in MAP) and created an extremely large set of new covariates from them by
combining in various ways (different spatial aggregations, temporal lags and summaries, and
mathematical transforms). From these, 32 different combinations were selected and those in turn
were used to generate 20 new compound covariate cubes.

These 20 covariate cubes form the input to Sam's Pf modelling. However they only cover Africa
and only up to the end of 2015. To run the modelling forward in time and for a global extent
we therefore need to repeat the generation process. Unfortunately the original code, written in IDL,
is somewhat unmaintainable and is quite firmly tied to the precise original folder structures
and filenames that were used last time round.

Therefore we are re-implementing the code from scratch based on the content of the published paper
and the existing code. The existing code can be found in the idl_code subfolder of this
repository.
