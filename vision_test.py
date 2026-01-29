from core.vision.vision_engine import VisionEngine

if __name__ == "__main__":
    vision = VisionEngine(fps=10, debug=True)
    vision.start()
