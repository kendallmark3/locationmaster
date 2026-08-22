import {useEffect, useRef, useState} from "react";
import {createRoot} from "react-dom/client";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import "./styles.css";

type Point = {id:string; label:string; category:string; symbol:string; longitude:number; latitude:number};

function App(){
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map|null>(null);
  const [intent,setIntent] = useState("");
  const [query,setQuery] = useState("");
  const [points,setPoints] = useState<Point[]>([]);

  useEffect(()=>{
    if(!mapContainer.current || mapRef.current) return;
    mapRef.current = new maplibregl.Map({
      container: mapContainer.current,
      // Dev-only public style. Replace with Amazon Location style URL in deployed config.
      style: "https://demotiles.maplibre.org/style.json",
      center: [-96.8,32.8],
      zoom: 3
    });
    mapRef.current.on("click",(e)=>{
      const label = window.prompt("Label this story point:");
      if(!label) return;
      setPoints(p=>[...p,{
        id: crypto.randomUUID(), label, category:"custom", symbol:"custom",
        longitude:e.lngLat.lng, latitude:e.lngLat.lat
      }]);
    });
    return ()=>mapRef.current?.remove();
  },[]);

  useEffect(()=>{
    if(!mapRef.current) return;
    const markers: maplibregl.Marker[] = [];
    points.forEach(p=>{
      const el=document.createElement("div");
      el.className="story-marker";
      el.title=p.label;
      const marker=new maplibregl.Marker({element:el})
        .setLngLat([p.longitude,p.latitude])
        .setPopup(new maplibregl.Popup().setText(p.label))
        .addTo(mapRef.current!);
      markers.push(marker);
    });
    return ()=>markers.forEach(m=>m.remove());
  },[points]);

  async function search(){
    const r=await fetch(`/api/geocode?q=${encodeURIComponent(query)}`);
    if(!r.ok) return alert("Geocode failed");
    const results=await r.json();
    if(!results.length) return alert("No result");
    const x=results[0];
    setPoints(p=>[...p,{
      id:crypto.randomUUID(),label:x.label,category:"subject",symbol:"subject",
      longitude:x.longitude,latitude:x.latitude
    }]);
    mapRef.current?.flyTo({center:[x.longitude,x.latitude],zoom:14});
  }

  return <div className="shell">
    <aside>
      <h1>Location Story</h1>
      <label>What story are you trying to tell?</label>
      <textarea value={intent} onChange={e=>setIntent(e.target.value)}
        placeholder="Build the strongest location story for this property..." />
      <label>Find a location</label>
      <div className="row"><input value={query} onChange={e=>setQuery(e.target.value)} /><button onClick={search}>Find</button></div>
      <p className="hint">Or click anywhere on the map to add a custom point.</p>
      <h2>Story Points</h2>
      {points.map((p)=><div className="point" key={p.id}>
        <input value={p.label} onChange={e=>setPoints(ps=>ps.map(x=>x.id===p.id?{...x,label:e.target.value}:x))}/>
        <select value={p.symbol} onChange={e=>setPoints(ps=>ps.map(x=>x.id===p.id?{...x,symbol:e.target.value}:x))}>
          {["subject","company","restaurant","coffee","golf","hotel","transit","school","employer","custom"].map(s=><option key={s}>{s}</option>)}
        </select>
        <button onClick={()=>setPoints(ps=>ps.filter(x=>x.id!==p.id))}>Remove</button>
      </div>)}
      <button className="primary" disabled={!intent || !points.length}>Save Story</button>
    </aside>
    <main ref={mapContainer}/>
  </div>
}

createRoot(document.getElementById("root")!).render(<App/>);
