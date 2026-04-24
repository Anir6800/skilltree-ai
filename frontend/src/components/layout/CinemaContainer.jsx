import React, { Suspense, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Stars, Float, Text } from '@react-three/drei';

const Scene = ({ children }) => {
  const cameraRef = useRef();
  
  useFrame((state) => {
    const scrollY = window.scrollY;
    // Zoom in/out based on scroll
    state.camera.position.z = 10 - scrollY * 0.01;
    // Subtle mouse parallax
    state.camera.position.x += (state.mouse.x * 2 - state.camera.position.x) * 0.05;
    state.camera.position.y += (state.mouse.y * 2 - state.camera.position.y) * 0.05;
    state.camera.lookAt(0, 0, 0);
  });

  return (
    <>
      <PerspectiveCamera makeDefault position={[0, 0, 10]} fov={50} />
      <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
      <Suspense fallback={null}>
        <Float speed={2} rotationIntensity={0.5} floatIntensity={1}>
          {children}
        </Float>
      </Suspense>
    </>
  );
};

const CinemaContainer = ({ children }) => {
  return (
    <div className="fixed inset-0 w-full h-[500vh] bg-background z-0">
      <div className="sticky top-0 w-full h-screen">
        <Canvas shadows gl={{ antialias: true, alpha: true }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} intensity={1} castShadow />
          <spotLight position={[-10, 20, 10]} angle={0.15} penumbra={1} intensity={1} />
          
          <Scene>{children}</Scene>

          {/* Global Cinematic Fog */}
          <fog attach="fog" args={['#030712', 5, 25]} />
        </Canvas>
      </div>
    </div>
  );
};

export default CinemaContainer;
