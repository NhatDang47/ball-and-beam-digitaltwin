🎛️ Ball and Beam: Hardware Digital Twin

Simulation for the Ball and Beam balancing system. This project is built to validate control algorithms and hardware design for a mechatronic system before deploying real firmware to a microcontroller.

📐 System Architecture

The system is designed following the Real-Time Safety principle in embedded systems:

Nonlinear Dynamics: Accurately simulates the motion equation of a solid steel ball rolling on a beam, incorporating rolling inertia compensation (Rolling Inertia) with coefficient B = 5/7, and friction forces.

Control Algorithm: Uses a Cascaded PID structure (Dual-loop PID):

Outer Loop: Position control.

Inner Loop: Angle control.

Includes output clamping and integrator anti-windup.

Digital Filtering: Applies an EMA low-pass filter to reduce measurement noise and smooth the derivative (D) term.

🛠️ Hardware Constraint Simulation (HAL)

The key difference of this Digital Twin is the integration of real hardware physical limitations into the digital environment:

Distance Sensor: Injects white noise (Gaussian Noise) and applies quantization based on millimeter resolution.

Motor Encoder: Discretizes the measured angle based on PPR (Pulses Per Revolution), recreating real-world step-like signal behavior.

Actuator: Limits the maximum motor RPM and quantizes the output signal according to PWM resolution (e.g., 8-bit / 255 levels).

🚀 Installation & Execution

The project uses uv as the dependency manager to ensure a consistent development environment.

1. Run from Source Code

Requirements: Python 3.12+ and uv installed.

# Install dependencies (NumPy, Pygame)
uv sync
# Or: uv add numpy pygame

# Run the project
uv run main.py
