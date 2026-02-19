// 3D Floating Elements Background using React Three Fiber
import React, { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float, MeshDistortMaterial, Sphere } from '@react-three/drei'
import * as THREE from 'three'

const FloatingShape = ({ position, color, speed }) => {
  const meshRef = useRef()

  useFrame((state) => {
    const t = state.clock.getElapsedTime()
    meshRef.current.rotation.x = Math.sin(t * speed) * 0.2
    meshRef.current.rotation.y = Math.cos(t * speed) * 0.2
  })

  return (
    <Float
      speed={speed}
      rotationIntensity={0.5}
      floatIntensity={0.5}
      floatingRange={[-0.5, 0.5]}
    >
      <Sphere ref={meshRef} args={[1, 32, 32]} position={position}>
        <MeshDistortMaterial
          color={color}
          attach="material"
          distort={0.4}
          speed={2}
          roughness={0.2}
          metalness={0.8}
        />
      </Sphere>
    </Float>
  )
}

const Scene3D = () => {
  const shapes = useMemo(
    () => [
      { position: [-4, 2, -5], color: '#3b82f6', speed: 0.5 },
      { position: [4, -2, -8], color: '#8b5cf6', speed: 0.7 },
      { position: [0, 3, -6], color: '#06b6d4', speed: 0.6 },
      { position: [-2, -3, -7], color: '#ec4899', speed: 0.8 },
      { position: [3, 1, -9], color: '#10b981', speed: 0.4 },
    ],
    []
  )

  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} intensity={1} />
      <pointLight position={[-10, -10, -10]} intensity={0.5} color="#3b82f6" />
      
      {shapes.map((shape, i) => (
        <FloatingShape key={i} {...shape} />
      ))}
    </>
  )
}

export const Background3D = ({ className = '' }) => {
  return (
    <div className={`fixed inset-0 -z-10 ${className}`}>
      <Canvas
        camera={{ position: [0, 0, 10], fov: 50 }}
        gl={{ alpha: true, antialias: true }}
        style={{ background: 'transparent' }}
      >
        <Scene3D />
      </Canvas>
    </div>
  )
}

export default Background3D
