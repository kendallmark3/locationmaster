import {useEffect, useRef, useState} from "react";
import {createRoot} from "react-dom/client";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import "./styles.css";

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

// maplibre-gl has no built-in resolver for Mapbox's proprietary "mapbox://" style/source
// scheme, so we use Mapbox's plain-HTTPS raster tile endpoint (Static Tiles API) instead —
// it's a normal XYZ raster source, no extra library or URL-rewriting needed.
const MAP_STYLE: maplibregl.StyleSpecification | string = MAPBOX_TOKEN
  ? {
      version: 8,
      sources: {
        "mapbox-raster": {
          type: "raster",
          tiles: [`https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/256/{z}/{x}/{y}@2x?access_token=${MAPBOX_TOKEN}`],
          tileSize: 256,
          attribution: "© Mapbox © OpenStreetMap"
        }
      },
      layers: [{id: "mapbox-raster-layer", type: "raster", source: "mapbox-raster"}]
    }
  // Dev-only public fallback (full street-level detail, no key required) when no Mapbox
  // token is configured. Replace with Amazon Location style URL in deployed config.
  : "https://tiles.openfreemap.org/styles/positron";

type Point = {
  id:string; label:string; category:string; symbol:string;
  longitude:number; latitude:number;
  coordinateSource:"geocoder"|"map_click"|"import";
  providerPlaceId?:string|null;
  notes?:string;
};

const NEARBY_CATEGORIES: {id:string; label:string}[] = [
  {id:"coffee", label:"Coffee"},
  {id:"restaurant", label:"Restaurants"},
  {id:"school", label:"Schools"},
  {id:"park", label:"Parks"},
  {id:"transit", label:"Transit"},
  {id:"hotel", label:"Hotels"},
  {id:"grocery", label:"Grocery"},
  {id:"healthcare", label:"Healthcare"},
  {id:"entertainment", label:"Entertainment"},
  {id:"shopping", label:"Shopping"},
  {id:"community", label:"Community"},
];

const SYMBOL_COLORS: Record<string,string> = {
  subject:"#111111", coffee:"#6f4e37", restaurant:"#e2725b", golf:"#2f855a",
  school:"#2b6cb0", park:"#2f855a", transit:"#6b46c1", hotel:"#b7791f",
  grocery:"#2c7a7b", company:"#4a5568", employer:"#4a5568", custom:"#718096",
  healthcare:"#dc2626", entertainment:"#db2777", shopping:"#f59e0b", community:"#0891b2",
};

const SYMBOL_LABELS: Record<string,string> = {
  subject:"Home", coffee:"Coffee", restaurant:"Restaurants", golf:"Golf",
  school:"Schools", park:"Parks", transit:"Transit", hotel:"Hotels",
  grocery:"Grocery", company:"Company", employer:"Employer", custom:"Other",
  healthcare:"Healthcare", entertainment:"Entertainment", shopping:"Shopping", community:"Community",
};

// MapLibre "match" expression built from SYMBOL_COLORS so the two never drift apart.
const CIRCLE_COLOR_EXPR = [
  "match", ["get","symbol"],
  ...Object.entries(SYMBOL_COLORS).flatMap(([symbol,color])=>[symbol,color]),
  SYMBOL_COLORS.custom,
] as unknown as maplibregl.ExpressionSpecification;

function App(){
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map|null>(null);
  const [name,setName] = useState("");
  const [intent,setIntent] = useState("");
  const [query,setQuery] = useState("");
  const [points,setPoints] = useState<Point[]>([]);
  const [projectId,setProjectId] = useState<string|null>(null);
  const [savedVersion,setSavedVersion] = useState<number|null>(null);
  const [narrative,setNarrative] = useState<string|null>(null);
  const [narrativeLoading,setNarrativeLoading] = useState(false);

  type CapStep = {name:string; status:string; detail?:string};
  type CapResult = {success:boolean; workflow?:string; steps?:CapStep[]; result?:{setup:string;punchline:string}; failedStep?:string; message?:string};
  const [capResult,setCapResult] = useState<CapResult|null>(null);
  const [capLoading,setCapLoading] = useState(false);

  async function runCapabilityCheck(){
    setCapLoading(true);
    setCapResult(null);
    try{
      const r = await fetch("/api/capability-check",{method:"POST"});
      const body = await r.json();
      setCapResult(body);
    } catch(e){
      setCapResult({success:false, message:String(e)});
    } finally {
      setCapLoading(false);
    }
  }

  useEffect(()=>{
    if(!mapContainer.current || mapRef.current) return;
    mapRef.current = new maplibregl.Map({
      container: mapContainer.current,
      style: MAP_STYLE,
      center: [-96.8,32.8],
      zoom: 3,
      // Required to read pixels back out via getCanvas() for the image export below —
      // WebGL clears the drawing buffer after compositing to screen otherwise, and a
      // captured frame comes back blank.
      canvasContextAttributes: {preserveDrawingBuffer: true},
    });
    mapRef.current.on("click",(e)=>{
      // Don't prompt for a new point when the click landed on an existing one — the
      // story-points-circle layer's own click handler (added once points render) shows
      // that point's popup instead.
      const hit = mapRef.current!.getLayer("story-points-circle")
        ? mapRef.current!.queryRenderedFeatures(e.point, {layers:["story-points-circle"]})
        : [];
      if(hit.length) return;
      const label = window.prompt("Label this story point:");
      if(!label) return;
      setPoints(p=>[...p,{
        id: crypto.randomUUID(), label, category:"custom", symbol:"custom",
        longitude:e.lngLat.lng, latitude:e.lngLat.lat, coordinateSource:"map_click"
      }]);
    });
    return ()=>mapRef.current?.remove();
  },[]);

  useEffect(()=>{
    const id = new URLSearchParams(window.location.search).get("project");
    if(!id) return;
    fetch(`/api/projects/${id}`).then(r=>r.ok ? r.json() : Promise.reject())
      .then(p=>{
        setProjectId(p.id);
        setName(p.name);
        setIntent(p.rawIntent);
        setPoints(p.points);
        setSavedVersion(p.version);
        if(p.center) mapRef.current?.jumpTo({center:p.center, zoom:p.zoom});
      })
      .catch(()=>alert("Could not load project"));
  },[]);

  async function save(){
    const center = mapRef.current ? [mapRef.current.getCenter().lng, mapRef.current.getCenter().lat] : null;
    const zoom = mapRef.current?.getZoom() ?? 10;
    let id = projectId;
    if(!id){
      const r = await fetch("/api/projects",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name,rawIntent:intent})});
      if(!r.ok) return alert("Could not create project");
      id = (await r.json()).id;
      setProjectId(id);
    }
    const r2 = await fetch(`/api/projects/${id}`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({name,rawIntent:intent,points,center,zoom})});
    if(!r2.ok) return alert("Save failed");
    const saved = await r2.json();
    setSavedVersion(saved.version);
    const url = new URL(window.location.href);
    url.searchParams.set("project", id!);
    window.history.replaceState({},"",url);
  }

  const [exporting,setExporting] = useState(false);

  async function exportImage(){
    if(!projectId || savedVersion==null || !mapRef.current) return;
    setExporting(true);
    try{
      // Hits the export-boundary validation (contracts/coordinate provenance) the backend
      // already enforces — but the file we actually hand the user is captured client-side
      // from the live map below, so it shows real basemap tiles instead of the backend's
      // schematic PIL-drawn placeholder.
      const r = await fetch(`/api/projects/${projectId}/export`,{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({projectId, projectVersion:savedVersion, format:"png"})
      });
      if(!r.ok){
        const body = await r.json().catch(()=>({}));
        const detail = body.detail;
        const message = detail && typeof detail==="object" && detail.errors
          ? detail.errors.join("\n")
          : (typeof detail==="string" ? detail : "Export failed.");
        return alert(message);
      }

      const map = mapRef.current;
      const mapCanvas = map.getCanvas();
      const dpr = window.devicePixelRatio || 1;
      const headerH = Math.round(64 * dpr);
      const out = document.createElement("canvas");
      out.width = mapCanvas.width;
      out.height = mapCanvas.height + headerH;
      const ctx = out.getContext("2d")!;

      ctx.fillStyle = "#f6f7fb";
      ctx.fillRect(0, 0, out.width, out.height);
      ctx.fillStyle = "#111827";
      ctx.font = `${Math.round(20*dpr)}px sans-serif`;
      ctx.fillText(name || "Untitled", 16*dpr, 26*dpr);
      ctx.fillStyle = "#374151";
      ctx.font = `${Math.round(13*dpr)}px sans-serif`;
      ctx.fillText(intent || "", 16*dpr, 48*dpr);
      ctx.drawImage(mapCanvas, 0, headerH);

      points.forEach(p=>{
        const proj = map.project([p.longitude, p.latitude]);
        const px = proj.x*dpr, py = proj.y*dpr + headerH;
        const radius = (p.symbol==="subject" ? 8 : 6) * dpr;
        ctx.beginPath();
        ctx.arc(px, py, radius, 0, Math.PI*2);
        ctx.fillStyle = SYMBOL_COLORS[p.symbol] ?? SYMBOL_COLORS.custom;
        ctx.fill();
        ctx.lineWidth = 2*dpr;
        ctx.strokeStyle = "#ffffff";
        ctx.stroke();
        ctx.fillStyle = "#111827";
        ctx.font = `${Math.round(12*dpr)}px sans-serif`;
        ctx.fillText(p.label, px + radius + 4, py + 4*dpr);
      });

      out.toBlob(blob=>{
        if(!blob) return alert("Could not render the export image.");
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${name || "location-story"}.png`;
        a.click();
        URL.revokeObjectURL(url);
      }, "image/png");
    } finally {
      setExporting(false);
    }
  }

  async function generateNarrative(){
    if(!projectId) return;
    setNarrativeLoading(true);
    setNarrative(null);
    try{
      const r = await fetch(`/api/projects/${projectId}/narrative`,{method:"POST"});
      const body = await r.json();
      if(!r.ok) return alert(body.detail ?? "Could not generate a narrative.");
      setNarrative(body.narrative);
    } finally {
      setNarrativeLoading(false);
    }
  }

  const pointsRef = useRef<Point[]>([]);
  useEffect(()=>{ pointsRef.current = points; },[points]);

  // Rendered as a native MapLibre symbol layer (not individual DOM Markers) so its
  // built-in label-collision handling applies: a label only draws when there's room for
  // it, and the dot stays visible either way — with 30-50 points that's the difference
  // between a readable map and a smear of overlapping text.
  useEffect(()=>{
    const map = mapRef.current;
    if(!map) return;
    const geojson = {
      type: "FeatureCollection" as const,
      features: points.map(p=>({
        type: "Feature" as const,
        geometry: {type: "Point" as const, coordinates: [p.longitude, p.latitude]},
        properties: {label: p.label, symbol: p.symbol},
      })),
    };

    function upsert(){
      const source = map!.getSource("story-points") as maplibregl.GeoJSONSource | undefined;
      if(source){ source.setData(geojson as GeoJSON.FeatureCollection); return; }

      map!.addSource("story-points", {type:"geojson", data: geojson as GeoJSON.FeatureCollection});
      map!.addLayer({
        id: "story-points-circle",
        type: "circle",
        source: "story-points",
        paint: {
          "circle-radius": ["match", ["get","symbol"], "subject", 10, 7],
          "circle-color": CIRCLE_COLOR_EXPR,
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 2,
        },
      });
      map!.addLayer({
        id: "story-points-label",
        type: "symbol",
        source: "story-points",
        layout: {
          "text-field": ["get","label"],
          "text-size": 11,
          "text-offset": [0, 1.3],
          "text-anchor": "top",
          "text-allow-overlap": false,
          "text-optional": true,
        },
        paint: {
          "text-color": "#111827",
          "text-halo-color": "#ffffff",
          "text-halo-width": 1.4,
        },
      });
      map!.on("click","story-points-circle",(e)=>{
        const f = e.features?.[0];
        if(!f || f.geometry.type!=="Point") return;
        new maplibregl.Popup()
          .setLngLat(f.geometry.coordinates as [number,number])
          .setText(String(f.properties?.label ?? ""))
          .addTo(map!);
      });
      map!.on("mouseenter","story-points-circle",()=>{ map!.getCanvas().style.cursor="pointer"; });
      map!.on("mouseleave","story-points-circle",()=>{ map!.getCanvas().style.cursor=""; });
    }

    if(map.isStyleLoaded()) upsert(); else map.once("load", upsert);
  },[points]);

  const [nearbyLoading,setNearbyLoading] = useState<string|null>(null);
  const subjectPoint = points.find(p=>p.category==="subject") ?? points[0];

  // Fetches nearby places and appends them to state; returns what it added so callers
  // chaining several of these in a row (useMyLocation) can accumulate locally instead of
  // reading back out of `points`/`pointsRef`, which lag behind a tight loop of awaits.
  async function fetchNearby(category: string, pos: {lng:number; lat:number}, existing: Point[]): Promise<Point[]> {
    const r = await fetch(`/api/places/nearby?lng=${pos.lng}&lat=${pos.lat}&category=${category}`);
    if(!r.ok){ alert((await r.json()).detail ?? "Could not fetch nearby places."); return []; }
    const results: {label:string; longitude:number; latitude:number; place_id:string}[] = await r.json();
    const known = new Set(existing.map(p=>p.providerPlaceId).filter(Boolean));
    return results
      .filter(x=>!known.has(x.place_id))
      .map(x=>({
        id: crypto.randomUUID(), label: x.label, category, symbol: category,
        longitude: x.longitude, latitude: x.latitude,
        coordinateSource: "geocoder" as const, providerPlaceId: x.place_id,
      }));
  }

  function fitToPoints(pts: Point[]){
    if(!pts.length) return;
    const bounds = new maplibregl.LngLatBounds();
    pts.forEach(p=>bounds.extend([p.longitude,p.latitude]));
    mapRef.current?.fitBounds(bounds, {padding:60, maxZoom:15, duration:800});
  }

  async function addNearby(category: string){
    if(!subjectPoint) return;
    setNearbyLoading(category);
    try{
      const fresh = await fetchNearby(category, {lng:subjectPoint.longitude, lat:subjectPoint.latitude}, pointsRef.current);
      if(!fresh.length) return alert(`No new nearby ${category} found.`);
      setPoints(ps=>[...ps, ...fresh]);
      fitToPoints([...pointsRef.current, ...fresh]);
    } finally {
      setNearbyLoading(null);
    }
  }

  const [locating,setLocating] = useState(false);
  const [intentSummary,setIntentSummary] = useState<string|null>(null);
  const [interpreting,setInterpreting] = useState(false);

  // AI picks which supported categories the free-text intent implies; it never sees or
  // returns coordinates — fetchNearby (deterministic search) is what actually resolves a
  // category to real places, per ADR-001.
  async function interpretIntent(intentText: string): Promise<string[]> {
    const r = await fetch("/api/intent/interpret", {
      method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({intent:intentText})
    });
    if(!r.ok){ alert((await r.json()).detail ?? "Could not interpret intent."); return []; }
    const body = await r.json();
    setIntentSummary(body.summary || null);
    return body.categories ?? [];
  }

  async function buildFromIntent(){
    if(!intent.trim() || !subjectPoint) return;
    setInterpreting(true);
    try{
      const categories = await interpretIntent(intent);
      if(!categories.length){
        return alert("Couldn't find specific categories in that intent — try mentioning things like restaurants, schools, parks, healthcare, etc.");
      }
      let accumulated = pointsRef.current;
      for(const category of categories){
        setNearbyLoading(category);
        const fresh = await fetchNearby(category, {lng:subjectPoint.longitude, lat:subjectPoint.latitude}, accumulated);
        accumulated = [...accumulated, ...fresh];
      }
      setNearbyLoading(null);
      setPoints(accumulated);
      fitToPoints(accumulated);
    } finally {
      setInterpreting(false);
    }
  }

  async function useMyLocation(){
    if(!navigator.geolocation) return alert("Geolocation is not available in this browser.");
    setLocating(true);
    navigator.geolocation.getCurrentPosition(async (pos)=>{
      try{
        const {longitude:lng, latitude:lat} = pos.coords;
        const r = await fetch(`/api/reverse-geocode?lng=${lng}&lat=${lat}`);
        if(!r.ok){ alert((await r.json()).detail ?? "Could not determine your address."); return; }
        const place = await r.json();
        setName(place.label);
        // Don't clobber an intent the user already wrote — only fill the default when empty.
        const effectiveIntent = intent.trim() || `Show why ${place.label} is a great place to call home.`;
        if(!intent.trim()) setIntent(effectiveIntent);
        const subject: Point = {
          id: crypto.randomUUID(), label: place.label, category:"subject", symbol:"subject",
          longitude: place.longitude, latitude: place.latitude,
          coordinateSource:"geocoder", providerPlaceId: place.place_id ?? null,
        };
        mapRef.current?.flyTo({center:[place.longitude, place.latitude], zoom:14});

        let categories = ["coffee","restaurant","school","park"];
        if(intent.trim()){
          const interpreted = await interpretIntent(effectiveIntent);
          if(interpreted.length) categories = interpreted;
        }

        let accumulated = [subject];
        for(const category of categories){
          setNearbyLoading(category);
          const fresh = await fetchNearby(category, {lng:place.longitude, lat:place.latitude}, accumulated);
          accumulated = [...accumulated, ...fresh];
        }
        setNearbyLoading(null);
        setPoints(accumulated);
        fitToPoints(accumulated);
      } finally {
        setLocating(false);
      }
    }, (err)=>{
      setLocating(false);
      alert(`Could not get your location: ${err.message}`);
    });
  }

  async function search(){
    const r=await fetch(`/api/geocode?q=${encodeURIComponent(query)}`);
    if(!r.ok) return alert("Geocode failed");
    const results=await r.json();
    if(!results.length) return alert("No result");
    const x=results[0];
    setPoints(p=>[...p,{
      id:crypto.randomUUID(),label:x.label,category:"subject",symbol:"subject",
      longitude:x.longitude,latitude:x.latitude,
      coordinateSource:"geocoder",providerPlaceId:x.place_id ?? null
    }]);
    mapRef.current?.flyTo({center:[x.longitude,x.latitude],zoom:14});
  }

  return <div className="shell">
    <aside>
      <h1>Location Story</h1>
      <button className="primary" onClick={useMyLocation} disabled={locating || nearbyLoading!=null}>
        {locating ? (nearbyLoading ? `Finding ${nearbyLoading}…` : "Locating…") : "Use my location — fill in everything"}
      </button>
      <p className="hint">Fills project name and subject point from your current location. Uses your intent above (if you've written one) to pick which nearby categories to add; otherwise defaults to coffee/restaurants/schools/parks.</p>
      <label>Project name</label>
      <input value={name} onChange={e=>setName(e.target.value)} placeholder="Q3 site selection story" />
      <label>What story are you trying to tell?</label>
      <textarea value={intent} onChange={e=>setIntent(e.target.value)}
        placeholder="Build the strongest location story for this property..." />
      <button className="primary" disabled={!intent.trim() || !subjectPoint || interpreting || nearbyLoading!=null}
        onClick={buildFromIntent}>
        {interpreting ? (nearbyLoading ? `Finding ${nearbyLoading}…` : "Reading intent…") : "Build map from this intent"}
      </button>
      {!subjectPoint && <p className="hint">Find or place a subject point first, then this will pick relevant nearby categories from your intent.</p>}
      {intentSummary && <p className="hint">Map focus: {intentSummary}</p>}
      <label>Find a location</label>
      <div className="row"><input value={query} onChange={e=>setQuery(e.target.value)} /><button onClick={search}>Find</button></div>
      <p className="hint">Or click anywhere on the map to add a custom point.</p>
      <label>Add real nearby places</label>
      <div className="chip-row">
        {NEARBY_CATEGORIES.map(c=>
          <button key={c.id} className="chip" disabled={!subjectPoint || nearbyLoading!=null}
            onClick={()=>addNearby(c.id)}>
            {nearbyLoading===c.id ? "…" : c.label}
          </button>
        )}
      </div>
      {!subjectPoint && <p className="hint">Find or place a subject point first.</p>}
      <h2>Story Points</h2>
      {points.map((p)=><div className="point" key={p.id}>
        <input value={p.label} onChange={e=>setPoints(ps=>ps.map(x=>x.id===p.id?{...x,label:e.target.value}:x))}/>
        <select value={p.symbol} onChange={e=>setPoints(ps=>ps.map(x=>x.id===p.id?{...x,symbol:e.target.value}:x))}>
          {["subject","company","restaurant","coffee","golf","hotel","transit","school","employer","custom"].map(s=><option key={s}>{s}</option>)}
        </select>
        <button onClick={()=>setPoints(ps=>ps.filter(x=>x.id!==p.id))}>Remove</button>
        <textarea className="point-notes" value={p.notes ?? ""}
          onChange={e=>setPoints(ps=>ps.map(x=>x.id===p.id?{...x,notes:e.target.value}:x))}
          placeholder="Why does this point matter to the story? (used to write the relocation narrative)" />
      </div>)}
      <button className="primary" disabled={!name || !intent || !points.length} onClick={save}>Save Story</button>
      {savedVersion!=null && <p className="hint">Saved (version {savedVersion}).</p>}
      <button className="primary" disabled={!projectId || savedVersion==null || exporting} onClick={exportImage}>
        {exporting ? "Exporting…" : "Export Image"}
      </button>
      {!projectId && <p className="hint">Save the story first to export an image.</p>}
      <button className="primary" disabled={!projectId || narrativeLoading} onClick={generateNarrative}>
        {narrativeLoading ? "Writing..." : "Give me a reason to move here"}
      </button>
      {!projectId && <p className="hint">Save the story first to generate a reason.</p>}
      {narrative && <p className="narrative">{narrative}</p>}
      <h2>System Capabilities</h2>
      <button className="primary" disabled={capLoading} onClick={runCapabilityCheck}>
        {capLoading ? "Running capability workflow…" : "Run Capability Check"}
      </button>
      {capResult && <div className="cap-result">
        {capResult.steps?.map(s=><div key={s.name} className={`cap-step ${s.status}`}>
          {s.status==="passed"?"✓":"✕"} {s.name}{s.detail ? `: ${s.detail}` : ""}
        </div>)}
        {capResult.success && capResult.result && <div className="cap-joke">
          <strong>Joke of the Day</strong><br/>
          <em>{capResult.result.setup}</em><br/>
          {capResult.result.punchline}
        </div>}
        {!capResult.success && <div className="cap-error">
          ✕ {capResult.failedStep ?? "error"}: {capResult.message ?? "Capability check failed."}
        </div>}
      </div>}
    </aside>
    <main>
      {/* MapLibre owns this element's children imperatively — keep it free of any
          React-rendered siblings inside it, or reconciliation will fight MapLibre's
          own DOM writes. The legend below is a separate sibling, not a child. */}
      <div ref={mapContainer} className="map-canvas"/>
      {points.length > 0 && <div className="legend">
        {[...new Set(points.map(p=>p.symbol))].sort().map(sym=>
          <div key={sym} className="legend-row">
            <span className="legend-swatch" style={{background: SYMBOL_COLORS[sym] ?? SYMBOL_COLORS.custom}} />
            {SYMBOL_LABELS[sym] ?? sym}
          </div>
        )}
      </div>}
    </main>
  </div>
}

createRoot(document.getElementById("root")!).render(<App/>);
