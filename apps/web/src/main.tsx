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
];

const SYMBOL_COLORS: Record<string,string> = {
  subject:"#111111", coffee:"#6f4e37", restaurant:"#e2725b", golf:"#2f855a",
  school:"#2b6cb0", park:"#2f855a", transit:"#6b46c1", hotel:"#b7791f",
  grocery:"#2c7a7b", company:"#4a5568", employer:"#4a5568", custom:"#718096",
};

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

  useEffect(()=>{
    if(!mapContainer.current || mapRef.current) return;
    mapRef.current = new maplibregl.Map({
      container: mapContainer.current,
      style: MAP_STYLE,
      center: [-96.8,32.8],
      zoom: 3
    });
    mapRef.current.on("click",(e)=>{
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

  useEffect(()=>{
    if(!mapRef.current) return;
    const markers: maplibregl.Marker[] = [];
    points.forEach(p=>{
      const el=document.createElement("div");
      el.className="story-marker";
      el.style.background = SYMBOL_COLORS[p.symbol] ?? SYMBOL_COLORS.custom;
      if(p.symbol==="subject"){ el.style.width="30px"; el.style.height="30px"; }
      el.title=p.label;
      const marker=new maplibregl.Marker({element:el})
        .setLngLat([p.longitude,p.latitude])
        .setPopup(new maplibregl.Popup().setText(p.label))
        .addTo(mapRef.current!);
      markers.push(marker);
    });
    return ()=>markers.forEach(m=>m.remove());
  },[points]);

  const [nearbyLoading,setNearbyLoading] = useState<string|null>(null);
  const subjectPoint = points.find(p=>p.category==="subject") ?? points[0];

  async function addNearby(category: string){
    if(!subjectPoint) return;
    setNearbyLoading(category);
    try{
      const r = await fetch(`/api/places/nearby?lng=${subjectPoint.longitude}&lat=${subjectPoint.latitude}&category=${category}`);
      if(!r.ok) return alert((await r.json()).detail ?? "Could not fetch nearby places.");
      const results: {label:string; longitude:number; latitude:number; place_id:string}[] = await r.json();
      if(!results.length) return alert(`No nearby ${category} found.`);
      setPoints(ps=>{
        const known = new Set(ps.map(p=>p.providerPlaceId).filter(Boolean));
        const fresh = results
          .filter(x=>!known.has(x.place_id))
          .map(x=>({
            id: crypto.randomUUID(), label: x.label, category, symbol: category,
            longitude: x.longitude, latitude: x.latitude,
            coordinateSource: "geocoder" as const, providerPlaceId: x.place_id,
          }));
        return [...ps, ...fresh];
      });
      const bounds = new maplibregl.LngLatBounds();
      [...points, ...results].forEach(p=>bounds.extend([p.longitude,p.latitude]));
      mapRef.current?.fitBounds(bounds, {padding:60, maxZoom:15, duration:800});
    } finally {
      setNearbyLoading(null);
    }
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
      <label>Project name</label>
      <input value={name} onChange={e=>setName(e.target.value)} placeholder="Q3 site selection story" />
      <label>What story are you trying to tell?</label>
      <textarea value={intent} onChange={e=>setIntent(e.target.value)}
        placeholder="Build the strongest location story for this property..." />
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
      <button className="primary" disabled={!projectId || narrativeLoading} onClick={generateNarrative}>
        {narrativeLoading ? "Writing..." : "Give me a reason to move here"}
      </button>
      {!projectId && <p className="hint">Save the story first to generate a reason.</p>}
      {narrative && <p className="narrative">{narrative}</p>}
    </aside>
    <main ref={mapContainer}/>
  </div>
}

createRoot(document.getElementById("root")!).render(<App/>);
