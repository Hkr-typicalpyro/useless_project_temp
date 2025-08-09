"use client"

import { useState, useEffect, useRef } from "react"
import { DotLottieReact } from "@lottiefiles/dotlottie-react"
import "@fontsource/noto-sans-malayalam/400.css"
import "@fontsource/noto-sans-malayalam/700.css"

function useHoverStyle() {
  const [hover, setHover] = useState(false)
  const onMouseEnter = () => setHover(true)
  const onMouseLeave = () => setHover(false)
  const style = {
    color: hover ? "#000" : "#9BBB58",
    backgroundColor: hover ? "#9BBB58" : "transparent",
    transition: "all 0.2s ease",
  }
  return { style, onMouseEnter, onMouseLeave }
}

const styles = {
  loadingContainer: {
    background: "#1a1a1a",
    height: "100vh",
    margin: 0,
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    color: "#9BBB58",
    fontFamily: "'Courier New', 'Monaco', 'Menlo', monospace",
    letterSpacing: "0.1em",
  },
  loadingAnimation: {
    width: 120,
    height: 120,
    filter: "sepia(1) hue-rotate(70deg) saturate(2) brightness(0.8)",
    opacity: 0.9,
  },
  loadingText: {
    marginTop: 20,
    fontSize: 14,
    fontWeight: 400,
    textTransform: "uppercase",
    color: "#9BBB58",
    fontFamily: "'Courier New', monospace",
    letterSpacing: "0.15em",
  },
  appContainer: {
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    width: "100vw",
    padding: "20px",
    background: "#1a1a1a",
    color: "#9BBB58",
    userSelect: "none",
    gap: 30,
    fontFamily: "'Courier New', monospace",
    position: "relative",
    overflow: "hidden",
  },
  screenOverlay: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background:
      "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(155, 187, 88, 0.03) 2px, rgba(155, 187, 88, 0.03) 4px)",
    pointerEvents: "none",
    zIndex: 1,
  },
  nokiaHeader: {
    textAlign: "center",
    marginBottom: 30,
    fontSize: 12,
    color: "#666",
    letterSpacing: "0.2em",
    textTransform: "uppercase",
    zIndex: 2,
    position: "relative",
  },
  animationWrapper: {
    width: "100%",
    maxWidth: "400px",
    display: "flex",
    justifyContent: "center",
    marginBottom: 30,
    filter: "sepia(1) hue-rotate(70deg) saturate(1.5) brightness(0.9)",
    zIndex: 2,
    position: "relative",
  },
  snakeAnimation: {
    width: "300px",
    height: "auto",
    opacity: 0.9,
  },
  title: {
    fontSize: "3rem",
    fontWeight: "bold",
    color: "#9BBB58",
    letterSpacing: "0.05em",
    textTransform: "none",
    margin: "0 0 40px 0",
    textAlign: "center",
    textShadow: "0 0 20px rgba(155, 187, 88, 0.4)",
    zIndex: 2,
    position: "relative",
    fontFamily: "'Noto Sans Malayalam', sans-serif",
    background: "linear-gradient(90deg, #9BBB58, #CDE47D)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    animation: "glow 2s ease-in-out infinite",
  },
  playButton: {
    width: "100%",
    maxWidth: "300px",
    padding: "20px 40px",
    fontSize: "1.2rem",
    fontWeight: "bold",
    color: "#9BBB58",
    backgroundColor: "transparent",
    border: "3px solid #9BBB58",
    borderRadius: "8px",
    cursor: "pointer",
    userSelect: "none",
    transition: "all 0.2s ease",
    fontFamily: "'Courier New', monospace",
    letterSpacing: "0.1em",
    textTransform: "uppercase",
    boxShadow: "0 0 20px rgba(155, 187, 88, 0.3)",
    zIndex: 2,
    position: "relative",
  },
  nokiaFooter: {
    marginTop: 40,
    textAlign: "center",
    fontSize: 10,
    color: "#666",
    letterSpacing: "0.3em",
    zIndex: 2,
    position: "relative",
  },
  vibration: {
    display: "inline-block",
    animation: "vibrate 0.3s linear infinite",
  },
}

const vibrationKeyframes = `
  @keyframes vibrate {
    0% { transform: translate(0); }
    20% { transform: translate(-0.5px, 0.5px); }
    40% { transform: translate(-0.5px, -0.5px); }
    60% { transform: translate(0.5px, 0.5px); }
    80% { transform: translate(0.5px, -0.5px); }
    100% { transform: translate(0); }
  }
  
  @keyframes glow {
    0%, 100% { text-shadow: 0 0 5px rgba(155, 187, 88, 0.3); }
    50% { text-shadow: 0 0 15px rgba(155, 187, 88, 0.6), 0 0 25px rgba(155, 187, 88, 0.3); }
  }
`

export default function NokiaSnakeApp() {
  const hover = useHoverStyle()
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [initialLoading, setInitialLoading] = useState(true)

  useEffect(() => {
    function resumeAudio() {
      if (audioRef.current) {
        audioRef.current.play()
      }
      window.removeEventListener("click", resumeAudio)
      window.removeEventListener("touchstart", resumeAudio)
    }

    if (initialLoading && audioRef.current) {
      const playPromise = audioRef.current.play()
      if (playPromise !== undefined) {
        playPromise.catch(() => {
          window.addEventListener("click", resumeAudio)
          window.addEventListener("touchstart", resumeAudio)
        })
      }
    }

    const timer = setTimeout(() => setInitialLoading(false), 2200)
    return () => {
      clearTimeout(timer)
      window.removeEventListener("click", resumeAudio)
      window.removeEventListener("touchstart", resumeAudio)
    }
  }, [initialLoading])

  const startGame = async () => {
    try {
      const response = await fetch("http://localhost:5000/start-game", { method: "POST" })
      const data = await response.json()
      console.log(data.status)
    } catch (error) {
      console.error("Error starting game:", error)
    }
  }

  if (initialLoading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.screenOverlay}></div>
        <audio ref={audioRef} src="/game.mp3" loop style={{ display: "none" }} />
        <div style={styles.nokiaHeader}>UseLess Project</div>
        <div style={{ textAlign: "center", zIndex: 2, position: "relative" }}>
          <DotLottieReact
            src="https://lottie.host/dd73cf65-706f-470e-a6d8-39954fd44416/QXRVNS62yO.lottie"
            loop
            autoplay
            style={styles.loadingAnimation}
            aria-label="Loading animation"
          />
          <p style={styles.loadingText}>Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <>
      <style>{vibrationKeyframes}</style>
      <div style={styles.appContainer}>
        <div style={styles.screenOverlay}></div>

        <div style={styles.nokiaHeader}>UseLess Project</div>

        <div style={styles.animationWrapper} aria-label="Snake animation">
          <DotLottieReact
            src="https://lottie.host/d9fac687-1f23-4046-9480-e206ba7004a1/z1j1YrXsiR.lottie"
            loop
            autoplay
            style={styles.snakeAnimation}
            aria-label="Snake animation"
          />
        </div>

        {/* Malayalam text with fixed spacing & glow */}
        <h1 style={styles.title}>
  "ഇനി ഞാൻ പറയും
  <br />
  നീയൊക്കെ കേൾക്കും"
</h1>

        <button
          onClick={startGame}
          style={{ ...styles.playButton, ...hover.style }}
          onMouseEnter={hover.onMouseEnter}
          onMouseLeave={hover.onMouseLeave}
          aria-label="Start Snake Game"
        >
          <span style={styles.vibration}>► Play Game</span>
        </button>

        <div style={styles.nokiaFooter}>Menu • Select • Back</div>
      </div>
    </>
  )
}
