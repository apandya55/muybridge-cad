/**
 * Parse a binary or ASCII STL ArrayBuffer into a THREE.BufferGeometry.
 * Kept as a standalone util so it can be used outside react-three/fiber.
 */
import * as THREE from "three";

function isASCII(buf: ArrayBuffer): boolean {
  const bytes = new Uint8Array(buf, 0, Math.min(256, buf.byteLength));
  for (const b of bytes) {
    if (b > 127) return false;
  }
  const text = new TextDecoder().decode(new Uint8Array(buf, 0, 256));
  return text.trimStart().startsWith("solid");
}

function parseASCII(text: string): THREE.BufferGeometry {
  const positions: number[] = [];
  const normals: number[] = [];
  const normalRe = /facet\s+normal\s+([\d.eE+\-]+)\s+([\d.eE+\-]+)\s+([\d.eE+\-]+)/g;
  const vertexRe = /vertex\s+([\d.eE+\-]+)\s+([\d.eE+\-]+)\s+([\d.eE+\-]+)/g;
  let nm: RegExpExecArray | null;
  let vm: RegExpExecArray | null;
  const textCopy = text;
  normalRe.lastIndex = 0;
  vertexRe.lastIndex = 0;
  while ((nm = normalRe.exec(textCopy)) !== null) {
    const nx = parseFloat(nm[1]), ny = parseFloat(nm[2]), nz = parseFloat(nm[3]);
    for (let v = 0; v < 3; v++) {
      vm = vertexRe.exec(textCopy);
      if (!vm) break;
      positions.push(parseFloat(vm[1]), parseFloat(vm[2]), parseFloat(vm[3]));
      normals.push(nx, ny, nz);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  return geo;
}

function parseBinary(buf: ArrayBuffer): THREE.BufferGeometry {
  const view = new DataView(buf);
  const triCount = view.getUint32(80, true);
  const positions: number[] = [];
  const normals: number[] = [];
  let offset = 84;
  for (let i = 0; i < triCount; i++) {
    const nx = view.getFloat32(offset, true);
    const ny = view.getFloat32(offset + 4, true);
    const nz = view.getFloat32(offset + 8, true);
    offset += 12;
    for (let v = 0; v < 3; v++) {
      positions.push(
        view.getFloat32(offset, true),
        view.getFloat32(offset + 4, true),
        view.getFloat32(offset + 8, true),
      );
      normals.push(nx, ny, nz);
      offset += 12;
    }
    offset += 2; // attribute byte count
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  return geo;
}

export function parseSTL(buf: ArrayBuffer): THREE.BufferGeometry {
  if (isASCII(buf)) {
    return parseASCII(new TextDecoder().decode(buf));
  }
  return parseBinary(buf);
}
