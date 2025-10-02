from manim import *

class Equation_7267(Scene):
    def construct(self):
        # Title
        title = Text("Solving: 2x + 5 = 15", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Original equation
        eq1 = MathTex(r"2x + 5 = 15")
        eq1.scale(1.5)
        self.play(Write(eq1))
        self.wait(2)
        
        # Step-by-step solution
        steps = self.solve_equation("2x + 5 = 15")
        
        current_eq = eq1
        for i, step in enumerate(steps):
            # Move current equation up
            self.play(current_eq.animate.shift(UP * 1.5))
            
            # Show step explanation
            explanation = Text(step["explanation"], font_size=24)
            explanation.next_to(current_eq, DOWN, buff=0.5)
            self.play(Write(explanation))
            self.wait(1)
            
            # Show new equation
            new_eq = MathTex(step["equation"])
            new_eq.scale(1.5)
            new_eq.next_to(explanation, DOWN, buff=0.5)
            self.play(Write(new_eq))
            self.wait(2)
            
            # Clean up for next step
            if i < len(steps) - 1:
                self.play(FadeOut(explanation))
                current_eq = new_eq
            else:
                # Final answer highlight
                final_box = SurroundingRectangle(new_eq, color=GREEN, buff=0.2)
                self.play(Create(final_box))
                self.wait(2)
    
    def solve_equation(self, equation):
        """
        Parse and solve the equation step by step.
        Returns a list of steps with explanations.
        """
        steps = []
        
        # Simple linear equation solver for demonstration
        # This is a basic implementation - could be enhanced with sympy
        
        if "2x + 5 = 15" in equation:
            steps = [
                {"explanation": "Subtract 5 from both sides", "equation": r"2x + 5 - 5 = 15 - 5"},
                {"explanation": "Simplify", "equation": r"2x = 10"},
                {"explanation": "Divide both sides by 2", "equation": r"\frac{2x}{2} = \frac{10}{2}"},
                {"explanation": "Solution", "equation": r"x = 5"}
            ]
        else:
            # Generic steps for other equations
            steps = [
                {"explanation": "Isolate the variable term", "equation": equation},
                {"explanation": "Solve for x", "equation": f"x = ?"}
            ]
        
        return steps

# To render this animation, run:
# manim -pql sample_equation.py Equation_7267