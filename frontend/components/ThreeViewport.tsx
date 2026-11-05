"use client";
import { useEffect, useMemo, useRef, useState, Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Grid, Bounds, Edges } from "@react-three/drei";
import * as THREE from "three";
import { parseSTL } from "@/lib/stlLoader";

export default function ThreeViewport({ stlUrl }: { stlUrl: string | null }) {
  const [geo, setGeo] = useState<THREE.BufferGeometry | null>(null);
  const [wire, setWire] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!stlUrl) {
      setGeo(null);
      setError(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(stlUrl);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const buf = await r.arrayBuffer();
        if (cancelled) return;
        const g = parseSTL(buf);
        g.computeVertexNormals();
        g.center();
        setGeo(g);
        setError(null);
      } catch (e) {
        setError(String(e));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [stlUrl]);

  return (
    <div className="relative h-full w-full">
      {stlUrl && geo ? (
        <Canvas
          camera={{ position: [80, 60, 100], fov: 35, near: 0.1, far: 5000 }}
          dpr={[1, 2]}
          gl={{ antialias: true }}
          style={{ background: "transparent" }}
        >
          <ambientLight intensity={0.55} />
          <directionalLight position={[60, 80, 40]} intensity={1.1} />
          <directionalLight position={[-40, -20, -30]} intensity={0.25} color="#56b4e9" />
          <Suspense fallback={null}>
            <Bounds fit clip observe margin={1.2}>
              <Part geo={geo} wire={wire} />
            </Bounds>
          </Suspense>
          <Grid
            args={[200, 200]}
            position={[0, -0.01, 0]}
            cellSize={5}
            cellColor="rgba(255,255,255,0.05)"
            sectionSize={25}
            sectionColor="rgba(86,180,233,0.15)"
            fadeDistance={220}
            infiniteGrid
          />
          <OrbitControls makeDefault enableDamping dampingFactor={0.12} />
        </Canvas>
      ) : (
        <div className="flex h-full min-h-[280px] items-center justify-center rounded-lg bg-overlay/30 border border-hi" role="status" aria-live="polite">
          <div className="text-center">
            <div className="font-mono text-xs text-lo">
              Model preview
            </div>
            <div className="mt-1 text-2xs text-lo">
              {error ? `Could not load the model: ${error}` : "Run a part to see the compiled model."}
            </div>
          </div>
        </div>
      )}

      {stlUrl && geo && (
        <div className="absolute right-3 top-3 inline-flex rounded-lg bg-overlay/70 border border-hi p-0.5 backdrop-blur">
          <button type="button" aria-pressed={!wire}
            onClick={() => setWire(false)}
            className={`rounded-md px-2 py-1 text-2xs ${!wire ? "bg-accent/15 text-accent" : "text-mid"}`}
          >
            Solid
          </button>
          <button type="button" aria-pressed={wire}
            onClick={() => setWire(true)}
            className={`rounded-md px-2 py-1 text-2xs ${wire ? "bg-accent/15 text-accent" : "text-mid"}`}
          >
            Wire
          </button>
        </div>
      )}
    </div>
  );
}

function Part({ geo, wire }: { geo: THREE.BufferGeometry; wire: boolean }) {
  const mat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: "#9aa6b8",
        metalness: 0.15,
        roughness: 0.65,
        flatShading: false,
      }),
    [],
  );
  return (
    <group>
      <mesh geometry={geo} material={mat} visible={!wire} castShadow receiveShadow />
      <Edges geometry={geo} threshold={15} color="#56b4e9" />
    </group>
  );
}
