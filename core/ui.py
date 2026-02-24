import pygame
import math

class SimulationUI:
    def __init__(self, width=1200, height=650):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Ball and Beam - Hardware Digital Twin")
        self.font = pygame.font.SysFont("consolas", 14)
        self.font_bold = pygame.font.SysFont("consolas", 14, bold=True)
        self.clock = pygame.time.Clock()
        
        # Color Palette
        self.BG_VIEW = (25, 25, 25)
        self.BG_PANEL = (40, 45, 50)
        self.BEAM_COLOR = (200, 200, 200)
        self.BALL_COLOR = (255, 80, 80)
        self.TEXT_COLOR = (0, 255, 100)
        self.SP_COLOR = (80, 150, 255)
        self.EDIT_COLOR = (0, 255, 255)

        self.panel_width = 380
        self.active_param = None
        self.input_text = ""
        self.param_rects = {}

    def draw(self, state, setpoint, params_dict, is_dropped, L):
        # 1. Panel and Viewport
        self.screen.fill(self.BG_VIEW)
        pygame.draw.rect(self.screen, self.BG_PANEL, (0, 0, self.panel_width, self.height))
        pygame.draw.line(self.screen, (100, 100, 100), (self.panel_width, 0), (self.panel_width, self.height), 2)

        x, _, alpha, _ = state
        
        # 2. Viewport
        center_x = self.panel_width + (self.width - self.panel_width) // 2
        center_y = self.height // 2
        
        # Auto scale
        view_width = self.width - self.panel_width
        scale = (view_width * 0.7) / L 
        beam_length_px = L * scale

        # Draw beam
        dx = (beam_length_px / 2) * math.cos(alpha)
        dy = (beam_length_px / 2) * math.sin(alpha)
        p1 = (center_x - dx, center_y + dy) 
        p2 = (center_x + dx, center_y - dy)
        pygame.draw.line(self.screen, self.BEAM_COLOR, p1, p2, 8)
        pygame.draw.circle(self.screen, self.BEAM_COLOR, (center_x, center_y), 6) 
        
        # Draw sensor
        sensor_x = center_x - dx - 10*math.sin(alpha)
        sensor_y = center_y + dy - 10*math.cos(alpha)
        pygame.draw.rect(self.screen, (200, 200, 0), (sensor_x-5, sensor_y-5, 10, 10))

        # Draw setpoint
        sp_px = setpoint * scale
        sp_x_screen = center_x + sp_px * math.cos(alpha)
        sp_y_screen = center_y - sp_px * math.sin(alpha)
        pygame.draw.circle(self.screen, self.SP_COLOR, (int(sp_x_screen), int(sp_y_screen)), 5)

        # Draw ball
        ball_px = x * scale
        ball_x_screen = center_x + ball_px * math.cos(alpha)
        ball_y_screen = center_y - ball_px * math.sin(alpha)
        ball_radius = max(10, int(0.02 * scale)) # Bán kính giả định 2cm
        bx = ball_x_screen - (ball_radius + 4) * math.sin(alpha)
        by = ball_y_screen - (ball_radius + 4) * math.cos(alpha)
        pygame.draw.circle(self.screen, self.BALL_COLOR, (int(bx), int(by)), ball_radius)

        # 3. Control Panel
        if is_dropped:
            self._draw_text("SYSTEM HALTED! PRESS [SPACE]", 10, 15, (255, 50, 50), bold=True)
        else:
            self._draw_text("HARDWARE DIGITAL TWIN", 10, 15, (255, 200, 0), bold=True)
            self._draw_text("Click Viewport: Change Setpoint", 10, 35)
        
        self._draw_text(f"Real X: {x:+.3f}m | Ang: {math.degrees(alpha):+.1f}°", 10, 65, (200, 200, 200))
        
        hud_y = 100
        self.param_rects.clear()
        
        for i, (key, val) in enumerate(params_dict.items()):
            if "---" in key:
                hud_y += 10
                self._draw_text(key, 10, hud_y, (200, 150, 255), bold=True)
                hud_y += 25
                continue
                
            if self.active_param == key:
                text_str = f"> {key}: {self.input_text}_"
                color = self.EDIT_COLOR
            else:
                text_str = f"[ ] {key}: {val:.4f}"
                color = self.TEXT_COLOR
                
            surface = self.font.render(text_str, True, color)
            rect = surface.get_rect(topleft=(10, hud_y))
            hitbox = pygame.Rect(10, hud_y, self.panel_width - 20, 20)
            self.screen.blit(surface, rect)
            self.param_rects[key] = hitbox 
            hud_y += 25

        pygame.display.flip()

    def _draw_text(self, text, x, y, color=None, bold=False):
        if color is None: color = self.TEXT_COLOR
        font = self.font_bold if bold else self.font
        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))

    def handle_events(self):
        run_flag, reset_flag, new_setpoint, param_updates = True, False, None, {}

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run_flag = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                
                if mx < self.panel_width:
                    for key, rect in self.param_rects.items():
                        if rect.collidepoint(mx, my):
                            self.active_param = key
                            self.input_text = ""
                            break
                else:
                    self.active_param = None
                    center_x = self.panel_width + (self.width - self.panel_width) // 2
                    scale = ((self.width - self.panel_width) * 0.7) / 1.0 
                    new_setpoint = (mx - center_x) / scale 

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.active_param is None:
                    reset_flag = True
                elif self.active_param is not None:
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        try:
                            param_updates[self.active_param] = float(self.input_text)
                        except ValueError:
                            pass
                        self.active_param = None
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.active_param = None
                    elif event.unicode in '0123456789.-':
                        self.input_text += event.unicode

        return run_flag, reset_flag, new_setpoint, param_updates