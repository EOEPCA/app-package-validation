cwlVersion: v1.0
$graph:
- class: CommandLineTool
  id: stac
  requirements:
    InlineJavascriptRequirement: {}
    EnvVarRequirement:
        envDef:
          PATH: /opt/conda/envs/env_stac/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
          PYTHONPATH: /workspaces/vscode-binder/command-line-tools/stac:/home/jovyan/water-bodies/command-line-tools/stac:/workspaces/tb18-stac-citation/water-bodies/command-line-tools/stac
          PROJ_LIB: /opt/conda/envs/env_stac/lib/python3.9/site-packages/rasterio/proj_data
    ResourceRequirement:
        coresMax: 2
        ramMax: 2028
  hints:
    DockerRequirement:
        dockerPull: docker.terradue.com/wbd_stac@sha256:8f02148ae7f543f25360bc0c888d0ccfa42c5df2ce88482072db122b92e62da6
        dockerOutputDirectory: /tmp/mydir
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
