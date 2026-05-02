import { AlertTriangle, Box, LoaderCircle } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  AmbientLight,
  Box3,
  Color,
  DirectionalLight,
  GridHelper,
  PerspectiveCamera,
  Scene,
  Vector3,
  WebGLRenderer
} from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

interface GLBViewerProps {
  src: string | null;
}

type ViewerState = "empty" | "loading" | "ready" | "error" | "unsupported";

export function GLBViewer({ src }: GLBViewerProps) {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const [state, setState] = useState<ViewerState>(src ? "loading" : "empty");
  const [message, setMessage] = useState<string>("");

  useEffect(() => {
    if (!src) {
      setState("empty");
      setMessage("");
      return undefined;
    }
    const mount = mountRef.current;
    if (!mount) {
      return undefined;
    }
    const canvas = document.createElement("canvas");
    const gl = canvas.getContext("webgl2") || canvas.getContext("webgl");
    if (!gl) {
      setState("unsupported");
      setMessage("WebGL is not available in this browser.");
      return undefined;
    }

    setState("loading");
    setMessage("");

    const scene = new Scene();
    scene.background = new Color("#f8fafc");
    const camera = new PerspectiveCamera(45, 1, 0.1, 10000);
    camera.position.set(80, 60, 90);

    const renderer = new WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = "srgb";
    mount.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.screenSpacePanning = true;

    scene.add(new AmbientLight("#ffffff", 1.9));
    const key = new DirectionalLight("#ffffff", 2.4);
    key.position.set(60, 90, 120);
    scene.add(key);
    const fill = new DirectionalLight("#dfe8f2", 1.1);
    fill.position.set(-80, 45, -60);
    scene.add(fill);
    const grid = new GridHelper(180, 18, "#cfd8e3", "#e7ecf2");
    grid.position.y = -1;
    scene.add(grid);

    let frame = 0;
    let disposed = false;
    const resize = () => {
      const rect = mount.getBoundingClientRect();
      const width = Math.max(1, rect.width);
      const height = Math.max(1, rect.height);
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(mount);
    resize();

    const loader = new GLTFLoader();
    loader.load(
      src,
      (gltf) => {
        if (disposed) {
          return;
        }
        scene.add(gltf.scene);
        const bounds = new Box3().setFromObject(gltf.scene);
        const size = bounds.getSize(new Vector3());
        const center = bounds.getCenter(new Vector3());
        const maxDim = Math.max(size.x, size.y, size.z, 1);
        const distance = maxDim * 2.2;
        camera.position.set(center.x + distance, center.y + distance * 0.65, center.z + distance);
        camera.near = Math.max(maxDim / 1000, 0.1);
        camera.far = Math.max(maxDim * 20, 1000);
        camera.updateProjectionMatrix();
        controls.target.copy(center);
        controls.update();
        setState("ready");
      },
      undefined,
      (error) => {
        if (disposed) {
          return;
        }
        setState("error");
        setMessage(error instanceof Error ? error.message : "GLB could not be loaded.");
      }
    );

    const animate = () => {
      controls.update();
      renderer.render(scene, camera);
      frame = window.requestAnimationFrame(animate);
    };
    animate();

    return () => {
      disposed = true;
      window.cancelAnimationFrame(frame);
      observer.disconnect();
      controls.dispose();
      renderer.dispose();
      if (renderer.domElement.parentElement === mount) {
        mount.removeChild(renderer.domElement);
      }
      scene.traverse((object) => {
        const mesh = object as { geometry?: { dispose: () => void }; material?: unknown };
        mesh.geometry?.dispose();
        const material = mesh.material;
        if (Array.isArray(material)) {
          material.forEach((entry) => entry?.dispose?.());
        } else if (material && typeof material === "object" && "dispose" in material) {
          (material as { dispose: () => void }).dispose();
        }
      });
    };
  }, [src]);

  return (
    <div className="glb-stage" ref={mountRef}>
      {state !== "ready" ? (
        <div className={`viewer-state viewer-${state}`}>
          {state === "loading" ? (
            <LoaderCircle className="spin" size={22} aria-hidden="true" />
          ) : state === "error" || state === "unsupported" ? (
            <AlertTriangle size={22} aria-hidden="true" />
          ) : (
            <Box size={24} aria-hidden="true" />
          )}
          <p>{stateMessage(state, message)}</p>
        </div>
      ) : null}
    </div>
  );
}

function stateMessage(state: ViewerState, message: string): string {
  if (state === "loading") {
    return "Loading geometry";
  }
  if (state === "error") {
    return message || "GLB could not be loaded.";
  }
  if (state === "unsupported") {
    return message;
  }
  return "Geometry will appear after the first persisted revision.";
}
