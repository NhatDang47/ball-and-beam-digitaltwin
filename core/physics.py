import numpy as np

class BallAndBeamPlant:
    def __init__(self, length=1.0, dt=0.001):
        self.L = length
        self.g = 9.81
        self.dt = dt
        self.B = 5.0 / 7.0 
        self.max_omega = np.inf
        self.state = np.zeros(4)
        self.is_dropped = False

    def reset(self):
        self.state = np.zeros(4)
        self.is_dropped = False

    def step(self, motor_torque):
        if self.is_dropped:
            return self.state

        x, v, alpha, omega = self.state

        beam_damping = 0.5
        alpha_ddot = motor_torque - beam_damping * omega
        x_ddot = -self.B * self.g * np.sin(alpha) - 0.2 * v 

        v_next = v + x_ddot * self.dt
        x_next = x + v_next * self.dt
        
        omega_next = omega + alpha_ddot * self.dt
  
        omega_next = np.clip(omega_next, -self.max_omega, self.max_omega)
        
        alpha_next = alpha + omega_next * self.dt

        max_angle = np.deg2rad(45)
        if abs(alpha_next) > max_angle:
            alpha_next = np.sign(alpha_next) * max_angle
            omega_next = 0.0 

        if abs(x_next) > self.L / 2:
            self.is_dropped = True

        self.state = np.array([x_next, v_next, alpha_next, omega_next])
        return self.state