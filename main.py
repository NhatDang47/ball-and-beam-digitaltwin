import sys
import pygame
import random
import numpy as np
import math
from core.physics import BallAndBeamPlant
from core.controller import CascadedPID, EMAFilter
from core.ui import SimulationUI

def main():
    PHYSICS_DT = 0.001       
    RENDER_FPS = 60          
    STEPS_PER_FRAME = int((1.0 / RENDER_FPS) / PHYSICS_DT) 

    system_params = {
        "--- MODEL SPECIFICATIONS ---": 0,
        "Beam Length (m)": 0.8,
        "Motor Max RPM": 150.0,
        "Encoder PPR": 600.0,
        "PWM Resolution": 255.0,
        "Sensor Noise (m)": 0.003,
        "LPF Alpha (Sensor)": 0.1,
        "--- OUTER LOOP PID ---": 0,
        "Outer P": 0.8,
        "Outer I": 0.0,
        "Outer D": 2.5,
        "--- INNER LOOP PID ---": 0,
        "Inner P": 20.0,
        "Inner I": 0.0,
        "Inner D": 2.0
    }

    plant = BallAndBeamPlant(length=system_params["Beam Length (m)"], dt=PHYSICS_DT)
    pid = CascadedPID(dt=PHYSICS_DT)
    ui = SimulationUI()
    
    x_filter = EMAFilter(alpha=system_params["LPF Alpha (Sensor)"])
    omega_filter = EMAFilter(alpha=0.05) 

    setpoint_x = 0.0
    prev_measured_alpha = 0.0

    running = True
    while running:
        # --- PHASE 1 ---
        running, reset_flag, new_sp, param_updates = ui.handle_events()
        
        if reset_flag:
            plant.reset()
            pid.reset()
            setpoint_x = 0.0
            prev_measured_alpha = 0.0
            
        if new_sp is not None:
            actual_scale = ((ui.width - ui.panel_width) * 0.7) / plant.L
            new_sp = new_sp * (1.0 / plant.L) * plant.L # Re-normalize
            setpoint_x = max(-plant.L/2 + 0.05, min(plant.L/2 - 0.05, new_sp))
            
        if param_updates:
            system_params.update(param_updates)
            
            # Update Hardware Constraints
            plant.L = max(0.2, system_params["Beam Length (m)"]) # Min 20cm
            plant.max_omega = system_params["Motor Max RPM"] * 2 * np.pi / 60.0
            x_filter.alpha = system_params["LPF Alpha (Sensor)"]
            
            # Update PID
            pid.outer_pid.kp, pid.outer_pid.ki, pid.outer_pid.kd = system_params["Outer P"], system_params["Outer I"], system_params["Outer D"]
            pid.inner_pid.kp, pid.inner_pid.ki, pid.inner_pid.kd = system_params["Inner P"], system_params["Inner I"], system_params["Inner D"]

        # --- PHASE 2 ---
        if not plant.is_dropped:
            for _ in range(STEPS_PER_FRAME):
                true_x, true_v, true_alpha, true_omega = plant.state
                
                # ---------------------------------------------------------
                # H.A.L
                # ---------------------------------------------------------
                # 1. Sensor Noise + Resolution 1mm
                raw_x = true_x + random.uniform(-system_params["Sensor Noise (m)"], system_params["Sensor Noise (m)"])
                measured_x = round(raw_x * 1000) / 1000.0 
                filtered_x = x_filter.update(measured_x)
                
                # 2. Encoder
                PPR = max(1.0, system_params["Encoder PPR"])
                alpha_res = (2 * math.pi) / PPR
                measured_alpha = round(true_alpha / alpha_res) * alpha_res
                
                raw_omega = (measured_alpha - prev_measured_alpha) / PHYSICS_DT
                filtered_omega = omega_filter.update(raw_omega)
                prev_measured_alpha = measured_alpha

                # ---------------------------------------------------------
                # CONTROL ALGORITHM
                # ---------------------------------------------------------
                motor_cmd, _ = pid.compute(setpoint_x, filtered_x, true_v, measured_alpha, filtered_omega)
                
                # ---------------------------------------------------------
                # H.A.L: ACTUATOR
                # ---------------------------------------------------------

                max_torque = 50.0
                pwm_res = max(1.0, system_params["PWM Resolution"])
                
                pwm_val = round((motor_cmd / max_torque) * pwm_res)
                pwm_val = np.clip(pwm_val, -pwm_res, pwm_res)
                applied_torque = (pwm_val / pwm_res) * max_torque
                
                plant.step(applied_torque)
        
        # --- PHASE 3 ---

        ui.draw(plant.state, setpoint_x, system_params, plant.is_dropped, plant.L)
        ui.clock.tick(RENDER_FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()