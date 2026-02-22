"use client";

import { useEffect, useRef } from "react";
import { useTheme } from "@/lib/theme";

export default function ParticleBackground() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const { theme } = useTheme();

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let animationFrameId: number;

        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };

        window.addEventListener("resize", resize);
        resize();

        // Particle settings
        const particleCount = 100; // slightly more dense
        const connectionDistance = 200; // connect from further away
        const particles: { x: number; y: number; vx: number; vy: number; radius: number }[] = [];

        // Initialize particles
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.8, // Slightly faster drifting speed
                vy: (Math.random() - 0.5) * 0.8,
                radius: Math.random() * 2 + 1.5, // Much larger dots (1.5 to 3.5 radius)
            });
        }

        const draw = () => {
            // Clear canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Colors based on theme to match data science vibe (Blues and Purples)
            // Brighter particles
            const particleColor = theme === "dark" ? "rgba(96, 165, 250, 0.8)" : "rgba(59, 130, 246, 0.6)"; // Blue-400/500
            const lineColorRoot = theme === "dark" ? "167, 139, 250" : "139, 92, 246"; // Purple-400 base for connections

            particles.forEach((p, index) => {
                // Move particles
                p.x += p.vx;
                p.y += p.vy;

                // Bounce off edges smoothly
                if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
                if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

                // Draw particle
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = particleColor;
                ctx.fill();

                // Connect nearby particles
                for (let j = index + 1; j < particles.length; j++) {
                    const p2 = particles[j];
                    const dx = p.x - p2.x;
                    const dy = p.y - p2.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance < connectionDistance) {
                        // Opacity decreases as distance increases
                        const opacity = 1 - distance / connectionDistance;
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(p2.x, p2.y);
                        // Make lines thicker and more opaque
                        ctx.strokeStyle = `rgba(${lineColorRoot}, ${Math.min(opacity * 0.6, 0.8)})`;
                        ctx.lineWidth = 1.0;
                        ctx.stroke();
                    }
                }
            });

            animationFrameId = requestAnimationFrame(draw);
        };

        draw();

        return () => {
            cancelAnimationFrame(animationFrameId);
            window.removeEventListener("resize", resize);
        };
    }, [theme]);

    // Subtle opacity
    return (
        <canvas
            ref={canvasRef}
            className={`fixed inset-0 z-0 pointer-events-none transition-opacity duration-1000 ${theme === "dark" ? "opacity-30" : "opacity-15"
                }`}
        />
    );
}
