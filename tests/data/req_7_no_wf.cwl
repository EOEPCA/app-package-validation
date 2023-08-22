cwlVersion: v1.0
$namespaces:
  s: https://schema.org/
s:softwareVersion: 1.1.7
schemas:
  - http://schema.org/version/9.0/schemaorg-current-http.rdf
$graph:
  - class: CommandLineTool
    id: stac
    requirements:
      InlineJavascriptRequirement: {}
      EnvVarRequirement:
        envDef:
          PATH: /srv/conda/envs/env_stac/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
          PYTHONPATH: /workspaces/ogc-eo-application-package-hands-on/water-bodies/command-line-tools/stac:/home/jovyan/ogc-eo-application-package-hands-on/water-bodies/command-line-tools/stac:/workspaces/vscode-binder/command-line-tools/stac
          PROJ_LIB: /srv/conda/envs/env_stac/lib/python3.9/site-packages/rasterio/proj_data
      ResourceRequirement:
        coresMax: 2
        ramMax: 2028
    hints:
      DockerRequirement:
        dockerPull: ghcr.io/terradue/ogc-eo-application-package-hands-on/stac:1.1.7
    baseCommand: ["python", "-m", "app"]
    arguments: []
    inputs:
      item:
        type:
          type: array
          items: string
          inputBinding:
            prefix: --input-item
      rasters:
        type:
          type: array
          items: File
          inputBinding:
            prefix: --water-body
    outputs:
      stac_catalog:
        outputBinding:
          glob: .
        type: Directory
