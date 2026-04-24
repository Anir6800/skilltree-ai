import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Float, Sphere, MeshDistortMaterial } from '@react-three/drei';

const PulsingCore = () => {
  const mesh = useRef();
  const innerMesh = useRef();

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    mesh.current.rotation.x = Math.cos(t / 4) / 2;
    mesh.current.rotation.y = Math.sin(t / 4) / 2;
    mesh.current.rotation.z = Math.sin(t / 4) / 2;
    mesh.current.position.y = Math.sin(t / 2) / 4;
    
    innerMesh.current.rotation.x = -Math.cos(t / 2) / 2;
    innerMesh.current.rotation.y = -Math.sin(t / 2) / 2;
  });

  return (
    <group>
      <Float speed={2} rotationIntensity={1} floatIntensity={2}>
        <mesh ref={mesh}>
          <sphereGeometry args={[2, 64, 64]} />
          <MeshDistortMaterial
            color="#6366f1"
            attach="material"
            distort={0.4}
            speed={2}
            roughness={0}
            metalness={1}
          />
        </mesh>
      </Float>
      
      <mesh ref={innerMesh}>
        <sphereGeometry args={[1.2, 32, 32]} />
        <meshStandardMaterial
          color="#f43f5e"
          emissive="#f43f5e"
          emissiveIntensity={2}
          wireframe
        />
      </mesh>

      <pointLight position={[0, 0, 0]} intensity={2} color="#f43f5e" />
    </group>
  );
};

export default PulsingCore;
