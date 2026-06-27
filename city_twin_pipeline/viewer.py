from __future__ import annotations

from pathlib import Path


def write_static_viewer(output_dir: Path, layer_names: list[str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    layers_js = ",\n      ".join(f'"{layer}"' for layer in layer_names)
    layer_urls_js = ",\n      ".join(f'"{layer}": "../layers/{layer}.geojson"' for layer in layer_names)
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Shanghai City Digital Twin POC</title>
  <style>
    html, body {{ width: 100%; height: 100%; margin: 0; overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #e5edf3; color: #0f172a; }}
    #cesiumContainer, #fallbackMap {{ position: absolute; inset: 0; }}
    #fallbackMap {{ background: #e5edf3; }}
    .panel {{ position: absolute; left: 16px; top: 16px; width: min(380px, calc(100vw - 32px)); background: rgba(16, 22, 30, 0.88); color: #f8fafc; padding: 14px 16px; border-radius: 8px; box-shadow: 0 12px 30px rgba(0,0,0,.22); z-index: 2; }}
    .panel h1 {{ font-size: 15px; line-height: 1.25; margin: 0 0 10px; font-weight: 650; letter-spacing: 0; }}
    .panel dl {{ display: grid; grid-template-columns: 120px 1fr; gap: 6px 10px; margin: 0; font-size: 12px; line-height: 1.35; }}
    .panel dt {{ color: #94a3b8; }}
    .panel dd {{ margin: 0; color: #e2e8f0; }}
    .layer-list {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }}
    .layer-list button {{ border: 1px solid rgba(148,163,184,.35); background: rgba(15,23,42,.7); color: #e2e8f0; border-radius: 6px; padding: 5px 8px; font-size: 12px; line-height: 1; cursor: pointer; }}
    .layer-list button[aria-pressed="true"] {{ background: #0f766e; border-color: #2dd4bf; color: white; }}
    .mode {{ margin-top: 10px; font-size: 11px; color: #cbd5e1; }}
    svg {{ width: 100%; height: 100%; display: block; }}
  </style>
</head>
<body>
  <div id="fallbackMap"></div>
  <div id="cesiumContainer" hidden></div>
  <section class="panel" aria-label="POC status">
    <h1>Shanghai City Digital Twin POC</h1>
    <dl id="stats">
      <dt>Quality</dt><dd>loading</dd>
      <dt>Buildings</dt><dd>loading</dd>
      <dt>Roads</dt><dd>loading</dd>
      <dt>Water</dt><dd>loading</dd>
      <dt>POI</dt><dd>loading</dd>
    </dl>
    <div class="layer-list" id="layerControls"></div>
    <div class="mode" id="mode">Local SVG view loading</div>
  </section>
  <script>
    const layerNames = [
      {layers_js}
    ];
    const layerUrls = {{
      {layer_urls_js}
    }};
    const cssColors = {{
      buildings: "#64748b",
      roads: "#d97706",
      water: "#0284c7",
      green: "#16a34a",
      pois: "#dc2626"
    }};
    const activeLayers = new Set(layerNames);
    let layerData = {{}};
    let report = null;
    let cesiumViewer = null;
    const mode = document.getElementById("mode");

    async function loadJson(url) {{
      const response = await fetch(url);
      if (!response.ok) throw new Error(`${{url}} ${{response.status}}`);
      return response.json();
    }}

    async function init() {{
      const entries = await Promise.all(layerNames.map(async (name) => [name, await loadJson(layerUrls[name])]));
      layerData = Object.fromEntries(entries);
      report = await loadJson("../reports/quality_report.json");
      updateStats();
      controls();
      renderFallbackMap();
      loadCesium().then(renderCesium).catch(() => {{
        mode.textContent = "Local SVG view - Cesium CDN unavailable";
      }});
    }}

    function updateStats() {{
      const counts = report.counts || {{}};
      document.getElementById("stats").innerHTML = `
        <dt>Quality</dt><dd>${{report.status || "unknown"}}</dd>
        <dt>Buildings</dt><dd>${{counts.buildings ?? 0}}</dd>
        <dt>Roads</dt><dd>${{counts.roads ?? 0}}</dd>
        <dt>Water</dt><dd>${{counts.water ?? 0}}</dd>
        <dt>POI</dt><dd>${{counts.pois ?? 0}}</dd>
      `;
    }}

    function controls() {{
      const root = document.getElementById("layerControls");
      root.innerHTML = "";
      for (const name of layerNames) {{
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = name;
        button.setAttribute("aria-pressed", String(activeLayers.has(name)));
        button.addEventListener("click", async () => {{
          if (activeLayers.has(name)) activeLayers.delete(name);
          else activeLayers.add(name);
          button.setAttribute("aria-pressed", String(activeLayers.has(name)));
          renderFallbackMap();
          if (cesiumViewer) await renderCesium();
        }});
        root.appendChild(button);
      }}
    }}

    function renderFallbackMap() {{
      const features = [];
      for (const name of activeLayers) {{
        for (const feature of layerData[name]?.features || []) features.push([name, feature]);
      }}
      const coords = features.flatMap(([, feature]) => collectCoords(feature.geometry));
      if (!coords.length) return;
      const minLon = Math.min(...coords.map((c) => c[0]));
      const maxLon = Math.max(...coords.map((c) => c[0]));
      const minLat = Math.min(...coords.map((c) => c[1]));
      const maxLat = Math.max(...coords.map((c) => c[1]));
      const width = 1400;
      const height = 900;
      const pad = 44;
      const project = ([lon, lat]) => [
        pad + ((lon - minLon) / Math.max(maxLon - minLon, 1e-9)) * (width - pad * 2),
        height - pad - ((lat - minLat) / Math.max(maxLat - minLat, 1e-9)) * (height - pad * 2)
      ];
      const shapes = features.map(([name, feature]) => svgFeature(name, feature, project)).join("\\n");
      document.getElementById("fallbackMap").innerHTML = `
        <svg viewBox="0 0 ${{width}} ${{height}}" role="img" aria-label="Shanghai POC GeoJSON map">
          <rect width="${{width}}" height="${{height}}" fill="#e5edf3"/>
          ${{shapes}}
        </svg>`;
      mode.textContent = "Local SVG view";
    }}

    function svgFeature(name, feature, project) {{
      const color = cssColors[name] || "#334155";
      const geom = feature.geometry || {{}};
      if (geom.type === "Point") {{
        const [x, y] = project(geom.coordinates);
        return `<circle cx="${{x.toFixed(2)}}" cy="${{y.toFixed(2)}}" r="2.8" fill="${{color}}" opacity="0.9"/>`;
      }}
      if (geom.type === "LineString") {{
        const d = pathData(geom.coordinates, project);
        return `<path d="${{d}}" fill="none" stroke="${{color}}" stroke-width="1.8" opacity="0.75"/>`;
      }}
      if (geom.type === "Polygon") {{
        const d = pathData((geom.coordinates && geom.coordinates[0]) || [], project);
        const opacity = name === "buildings" ? "0.46" : "0.38";
        return `<path d="${{d}} Z" fill="${{color}}" stroke="${{color}}" stroke-width="0.5" opacity="${{opacity}}"/>`;
      }}
      return "";
    }}

    function pathData(coords, project) {{
      return (coords || []).map((coord, index) => {{
        const [x, y] = project(coord);
        return `${{index === 0 ? "M" : "L"}} ${{x.toFixed(2)}} ${{y.toFixed(2)}}`;
      }}).join(" ");
    }}

    function collectCoords(geometry) {{
      if (!geometry) return [];
      if (geometry.type === "Point") return [geometry.coordinates];
      if (geometry.type === "LineString") return geometry.coordinates || [];
      if (geometry.type === "Polygon") return (geometry.coordinates && geometry.coordinates[0]) || [];
      return [];
    }}

    function loadCesium() {{
      return new Promise((resolve, reject) => {{
        const timeout = setTimeout(() => reject(new Error("Cesium timeout")), 8000);
        const css = document.createElement("link");
        css.rel = "stylesheet";
        css.href = "https://cdnjs.cloudflare.com/ajax/libs/cesium/1.115.0/Widgets/widgets.min.css";
        document.head.appendChild(css);
        const script = document.createElement("script");
        script.src = "https://cdnjs.cloudflare.com/ajax/libs/cesium/1.115.0/Cesium.js";
        script.async = true;
        script.onload = () => {{
          clearTimeout(timeout);
          resolve();
        }};
        script.onerror = () => {{
          clearTimeout(timeout);
          reject(new Error("Cesium failed"));
        }};
        document.head.appendChild(script);
      }});
    }}

    async function renderCesium() {{
      if (!window.Cesium) return;
      document.getElementById("cesiumContainer").hidden = false;
      if (!cesiumViewer) {{
        cesiumViewer = new Cesium.Viewer("cesiumContainer", {{
          animation: false,
          timeline: false,
          baseLayerPicker: false,
          geocoder: false,
          homeButton: true,
          sceneModePicker: false,
          navigationHelpButton: false,
          infoBox: true,
          selectionIndicator: true
        }});
        cesiumViewer.scene.globe.baseColor = Cesium.Color.fromCssColorString("#e5edf3");
      }}
      cesiumViewer.dataSources.removeAll(true);
      for (const name of activeLayers) {{
        const ds = await Cesium.GeoJsonDataSource.load(layerUrls[name], {{ clampToGround: false }});
        ds.name = name;
        cesiumViewer.dataSources.add(ds);
        for (const entity of ds.entities.values) {{
          if (entity.polygon) {{
            entity.polygon.material = Cesium.Color.fromCssColorString(cssColors[name] || "#64748b").withAlpha(0.7);
            entity.polygon.outline = false;
            const height = entity.properties && entity.properties.height_m && entity.properties.height_m.getValue();
            if (name === "buildings" && typeof height === "number" && height > 0) entity.polygon.extrudedHeight = height;
          }}
          if (entity.polyline) {{
            entity.polyline.width = name === "roads" ? 2 : 1;
            entity.polyline.material = Cesium.Color.fromCssColorString(cssColors[name] || "#334155");
          }}
          if (entity.point) {{
            entity.point.pixelSize = 6;
            entity.point.color = Cesium.Color.fromCssColorString(cssColors[name] || "#dc2626");
          }}
        }}
      }}
      mode.textContent = "Cesium view";
      await cesiumViewer.zoomTo(cesiumViewer.dataSources);
    }}

    init().catch((error) => {{
      document.getElementById("stats").innerHTML = `<dt>Error</dt><dd>${{error.message}}</dd>`;
      mode.textContent = "Load failed";
      console.error(error);
    }});
  </script>
</body>
</html>
"""
    (output_dir / "index.html").write_text(html, encoding="utf-8")
