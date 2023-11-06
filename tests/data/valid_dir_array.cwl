$graph:
- baseCommand: opt-calibration
  class: CommandLineTool
  hints:
    DockerRequirement:
      dockerPull: docker.terradue.com/opt-calibration:dockerPullVersion
  id: clt
  arguments:
    - --add_composite
    - bav
    - --s_expressions
    - "ndvi: (where (& (> nir 0) (> red 0)) (norm_diff nir red) nil)"
    - --s_expressions
    - "ndwi: (where (& (> green 0) (> nir 0)) (norm_diff green nir) nil)"
    - --s_expressions
    - "ndbi: (where (& (> swir16 0) (> nir08 0)) (norm_diff swir16 nir08) nil)"
    - --s_expressions
    - "bav: (where (& (< (+ (/ (- swir16 swir22) (+ swir16 swir22) ) nir) 1000) (> swir16 1000) (< blue 1000) (< ndvi 0.3) (< ndwi 0.1) ) 1 0)"
  inputs:
    input_path:
      inputBinding:
        position: 1
        prefix: --input_path
      type: Directory
  outputs:
    results:
      outputBinding:
        glob: .
      type: Directory
  requirements:
    EnvVarRequirement:
      envDef:
        APP_DOCKER_IMAGE: docker.terradue.com/opt-calibration:dockerPullVersion
        APP_NAME: opt-calibration
        APP_PACKAGE: app-opt-calibration.0.15.14
        APP_VERSION: 0.15.14
        GDAL_CACHEMAX: '4096'
        GDAL_NUM_THREADS: ALL_CPUS
        LC_NUMERIC: C
        LD_LIBRARY_PATH: /srv/conda/envs/env_opt_calibration/conda-otb/lib/:/opt/anaconda/envs/env_opt_calibration/lib/:/usr/lib64
        OTB_APPLICATION_PATH: /srv/conda/envs/env_opt_calibration/conda-otb/lib/otb/applications
        OTB_MAX_RAM_HINT: '8192'
        PATH: /srv/conda/envs/env_opt_calibration/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/srv/conda/envs/env_opt_calibration/bin
        PREFIX: /srv/conda/envs/env_opt_calibration
        PYTHONPATH: /srv/conda/envs/env_opt_calibration/conda-otb/lib/python
        _PROJECT: GEP
    ResourceRequirement:
      coresMax: 8
      ramMax: 24576
  stderr: std.err
  stdout: std.out
- class: Workflow
  doc: This service provides calibrated images from optical EO data products. Optical
    calibrated products in output can be used as input for further thematic processing
    (e.g. co-location, co-registration).
  id: opt-calibration
  inputs:
    input_path:
      doc: Optical acquisition
      label: Optical acquisition
      type: Directory[]
  label: Optical Products Calibration
  outputs:
  - id: wf_outputs
    outputSource:
    - step_1/results
    type:
      items: Directory
      type: array
  requirements:
  - class: ScatterFeatureRequirement
  steps:
    step_1:
      in:
        input_path: input_path
      out:
      - results
      run: '#clt'
      scatter: input_path
      scatterMethod: dotproduct
$namespaces:
  s: https://schema.org/
cwlVersion: v1.0
s:softwareVersion: 0.15.14
schemas:
- http://schema.org/version/9.0/schemaorg-current-http.rdf