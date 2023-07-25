cwlVersion: v1.0
$namespaces:
  s: https://schema.org/
s:softwareVersion: 1.1.6
s:author:
  - class: s:Person
    s:name: Dow, John
    s:email: john.doe@somedomain.org
    s:affiliation: Planet Earth
s:contributor:
  - class: s:Person
    s:name: Doe, Jane
    s:email: jane.doe@somedomain.org
    s:affiliation: Planet Earth
schemas:
  - http://schema.org/version/9.0/schemaorg-current-http.rdf
$graph:
  - class: Workflow
    id: water_bodies
    label: Water bodies detection based on NDWI and otsu threshold
    doc: Water bodies detection based on NDWI and otsu threshold
    requirements:
      - class: ScatterFeatureRequirement
      - class: SubworkflowFeatureRequirement
    inputs:
      aoi:
        label: area of interest
        doc: area of interest as a bounding box
        type: string
      epsg:
        label: EPSG code
        doc: EPSG code
        type: string
        default: "EPSG:4326"
      stac_items:
        label: Sentinel-2 STAC items
        doc: list of Sentinel-2 COG STAC items
        type: string[]
    outputs:
      - id: stac_catalog
        outputSource:
          - node_stac/stac_catalog
        type: Directory
    steps:
      node_water_bodies:
        run: "#detect_water_body"
        in:
          item: stac_items
          aoi: aoi
          epsg: epsg
        out:
          - detected_water_body
        scatter: item
        scatterMethod: dotproduct
      node_stac:
        run: "#stac"
        in:
          item: stac_items
          rasters:
            source: node_water_bodies/detected_water_body
        out:
          - stac_catalog
  - class: Workflow
    id: detect_water_body
    label: Water body detection based on NDWI and otsu threshold
    doc: Water body detection based on NDWI and otsu threshold
    requirements:
      - class: ScatterFeatureRequirement
    inputs:
      aoi:
        doc: area of interest as a bounding box
        type: string
      epsg:
        doc: EPSG code
        type: string
        default: "EPSG:4326"
      bands:
        doc: bands used for the NDWI
        type: string[]
        default: ["green", "nir"]
      item:
        doc: STAC item
        type: string
    outputs:
      - id: detected_water_body
        outputSource:
          - node_otsu/binary_mask_item
        type: File
    steps:
      node_crop:
        run: "#crop"
        in:
          item: item
          aoi: aoi
          epsg: epsg
          band:
            default: ["green", "nir"]
        out:
          - cropped
        scatter: band
        scatterMethod: dotproduct
      node_normalized_difference:
        run: "#norm_diff"
        in:
          rasters:
            source: node_crop/cropped
        out:
          - ndwi
      node_otsu:
        run: "#otsu"
        in:
          raster:
            source: node_normalized_difference/ndwi
        out:
          - binary_mask_item
  - class: CommandLineTool
    id: crop
    requirements:
      InlineJavascriptRequirement: {}
      EnvVarRequirement:
        envDef:
          PATH: /opt/conda/envs/env_crop/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
          PYTHONPATH: /workspaces/vscode-binder/command-line-tools/crop:/home/jovyan/water-bodies/command-line-tools/crop:/workspaces/tb18-stac-citation/water-bodies/command-line-tools/crop
          PROJ_LIB: /opt/conda/envs/env_crop/share/proj/
      ResourceRequirement:
        coresMax: 2
        ramMax: 2028
    hints:
      DockerRequirement:
        dockerPull: docker.terradue.com/wbd_crop@sha256:f0f18a6d4b07c37ea5b969b9f42db44764f7d8112ddb178105e51313e5bd50ea
    baseCommand: ["python", "-m", "app"]
    arguments: []
    inputs:
      item:
        type: string
        inputBinding:
          prefix: --input-item
      aoi:
        type: string
        inputBinding:
          prefix: --aoi
      epsg:
        type: string
        inputBinding:
          prefix: --epsg
      band:
        type: string
        inputBinding:
          prefix: --band
    outputs:
      cropped:
        outputBinding:
          glob: '*.tif'
        type: File
  - class: CommandLineTool
    id: norm_diff
    requirements:
      InlineJavascriptRequirement: {}
      EnvVarRequirement:
        envDef:
          PATH: /opt/conda/envs/env_norm_diff/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
          PYTHONPATH: /workspaces/vscode-binder/command-line-tools/norm_diff:/home/jovyan/water-bodies/command-line-tools/norm_diff:/workspaces/tb18-stac-citation/water-bodies/command-line-tools/norm_diff
          PROJ_LIB: /opt/conda/envs/env_norm_diff/share/proj/
      ResourceRequirement:
        coresMax: 2
        ramMax: 2028
    hints:
      DockerRequirement:
        dockerPull: docker.terradue.com/wbd_norm_diff@sha256:8b27f6ec170d85856d242549d3288852e3057973ddd186a77db67c50d8d94ad6
    baseCommand: ["python", "-m", "app"]
    arguments: []
    inputs:
      rasters:
        type: File[]
        inputBinding:
          position: 1
    outputs:
      ndwi:
        outputBinding:
          glob: '*.tif'
        type: File
  - class: CommandLineTool
    id: otsu
    requirements:
      InlineJavascriptRequirement: {}
      EnvVarRequirement:
        envDef:
          PATH: /opt/conda/envs/env_otsu/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
          PYTHONPATH: /workspaces/vscode-binder/command-line-tools/otsu:/home/jovyan/water-bodies/command-line-tools/otsu:/workspaces/tb18-stac-citation/water-bodies/command-line-tools/otsu
          PROJ_LIB: /opt/conda/envs/env_otsu/share/proj/
      ResourceRequirement:
        coresMax: 2
        ramMax: 2028
    hints:
      DockerRequirement:
        dockerPull: docker.terradue.com/wbd_otsu@sha256:5bacca380d565ff6db34c030a6f7b78067db94d02f1cb6f763e855798e1025a5
    baseCommand: ["python", "-m", "app"]
    arguments: []
    inputs:
      raster:
        type: File
        inputBinding:
          position: 1
    outputs:
      binary_mask_item:
        outputBinding:
          glob: '*.tif'
        type: File
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
