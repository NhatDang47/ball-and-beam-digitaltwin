import numpy as np

class EMAFilter:
    """Exponential Moving Average"""
    def __init__(self, alpha=0.15):
        self.alpha = alpha
        self.value = 0.0
        self.initialized = False

    def update(self, measurement):
        if not self.initialized:
            self.value = measurement
            self.initialized = True
        else:
            self.value = (1 - self.alpha) * self.value + self.alpha * measurement
        return self.value

class PID:
    def __init__(self, kp, ki, kd, out_min, out_max, dt, max_i=None):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.out_min, self.out_max = out_min, out_max
        self.dt = dt
        self.integral = 0.0
 
        self.max_i = max_i if max_i is not None else float('inf')

    def compute(self, setpoint, process_variable, derivative_pv):
        error = setpoint - process_variable
        
        self.integral += error * self.dt
        self.integral = np.clip(self.integral, -self.max_i, self.max_i)
        i_term = self.ki * self.integral
        
        d_term = -self.kd * derivative_pv
        
        output = (self.kp * error) + i_term + d_term
        return np.clip(output, self.out_min, self.out_max)

    def reset(self):
        self.integral = 0.0

class CascadedPID:
    def __init__(self, dt):
        self.outer_pid = PID(kp=0.8, ki=0.02, kd=0.6, 
                             out_min=-0.4, out_max=0.4, 
                             dt=dt, max_i=10.0)
        
        self.inner_pid = PID(kp=20.0, ki=0.5, kd=8.0, 
                             out_min=-50.0, out_max=50.0, 
                             dt=dt, max_i=20.0)

    def compute(self, target_x, current_x, current_v, current_alpha, current_omega):
        target_alpha = -self.outer_pid.compute(target_x, current_x, derivative_pv=current_v)
        motor_cmd = self.inner_pid.compute(target_alpha, current_alpha, derivative_pv=current_omega)
        return motor_cmd, target_alpha

    def reset(self):
        self.outer_pid.reset()
        self.inner_pid.reset()