import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { MeshDistortMaterial, Sphere, Line, Html } from '@react-three/drei';
import * as THREE from 'three';

const PlanetNode = ({ position, title, color, isUnlocked }) => {
  const meshRef = useRef();
  
  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    meshRef.current.position.y += Math.sin(t * 2) * 0.002;
    meshRef.current.rotation.x = Math.cos(t * 0.5) * 0.1;
    meshRef.current.rotation.y = Math.sin(t * 0.5) * 0.1;
  });

  return (
    <group position={position}>
      <Sphere ref={meshRef} args={[0.8, 64, 64]}>
        <MeshDistortMaterial
          color={isUnlocked ? color : "#1e293b"}
          speed={isUnlocked ? 2 : 0}
          distort={0.3}
          radius={0.8}
          roughness={0.1}
          metalness={0.8}
          emissive={isUnlocked ? color : "#000"}
          emissiveIntensity={isUnlocked ? 0.5 : 0}
        />
      </Sphere>
      
      {/* Interactive Label */}
      <Html distanceFactor={10} position={[0, -1.2, 0]} center>
        <div className="flex flex-col items-center pointer-events-auto cursor-pointer">
          <span className={`text-xs font-bold uppercase tracking-widest ${isUnlocked ? 'text-white' : 'text-slate-500'}`}>
            {title}
          </span>
          {isUnlocked && <div className="w-8 h-0.5 bg-primary mt-1 shadow-[0_0_10px_#6366f1]" />}
        </div>
      </Html>
    </group>
  );
};

const SkillNexus = () => {
  const nodes = [
    { pos: [0, 0, 0], title: "Algorithms", color: "#6366f1", unlocked: true },
    { pos: [4, 3, -2], title: "Data Structures", color: "#f43f5e", unlocked: true },
    { pos: [-4, 2, -1], title: "Systems Design", color: "#10b981", unlocked: false },
    { pos: [0, 5, -4], title: "Machine Learning", color: "#f59e0b", unlocked: false },
    { pos: [-5, -3, -3], title: "Web Development", color: "#8b5cf6", unlocked: true },
  ];

  const connections = useMemo(() => {
    // Basic connections for mockup
    return [
      [nodes[0].pos, nodes[1].pos],
      [nodes[0].pos, nodes[2].pos],
      [nodes[1].pos, nodes[3].pos],
      [nodes[2].pos, nodes[4].pos],
    ];
  }, [nodes]);

  return (
    <group>
      {nodes.map((node, i) => (
        <PlanetNode 
          key={i} 
          position={node.pos} 
          title={node.title} 
          color={node.color} 
          isUnlocked={node.unlocked} 
        />
      ))}
      
      {connections.map((points, i) => (
        <Line
          key={i}
          points={points}
          color="#334155"
          lineWidth={0.5}
          transparent
          opacity={0.3}
        />
      ))}
    </group>
  );
};

export default SkillNexus;
