import os
from typing import Dict, Any, Optional

class MathTool:
    def __init__(self):
        self.app_id = os.getenv("WOLFRAM_APP_ID")

    def _wolfram(self, prompt: str) -> Optional[Dict[str, Any]]:
        if not self.app_id:
            return None
        try:
            import requests
            url = "https://api.wolframalpha.com/v1/result"
            r = requests.get(url, params={"i": prompt, "appid": self.app_id}, timeout=8)
            if r.ok:
                return {"tool":"wolframalpha","input":prompt,"result_text":r.text,"result_latex":None,"raw":{"endpoint":"short"}}
        except Exception:
            pass
        return None

    def _sympy(self, prompt: str) -> Dict[str, Any]:
        try:
            from sympy import Eq, sympify, symbols
            from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
            from sympy.solvers import solve as sympy_solve

            # Handle 'for' clauses (e.g., "x + 3y = 5 for x = 1")
            if ' for ' in prompt.lower():
                equation_part, subs_part = prompt.split(' for ', 1)
                try:
                    # Parse the equation part
                    eq_parts = [p.strip() for p in equation_part.split(';') if p.strip()]
                    eqs = [Eq(parse_expr(eq.split('=')[0].strip(), evaluate=True), 
                            parse_expr(eq.split('=')[1].strip(), evaluate=True)) 
                          for eq in eq_parts if '=' in eq]
                    
                    # Parse the substitution part
                    subs = {}
                    for sub in subs_part.split(','):
                        if '=' in sub:
                            var, val = sub.split('=', 1)
                            subs[var.strip()] = parse_expr(val.strip(), evaluate=True)
                    
                    # Apply substitutions
                    if subs and eqs:
                        eqs = [eq.subs(subs) for eq in eqs]
                    elif not eqs and '=' in equation_part:
                        # Handle case where equation is in the first part but wasn't split properly
                        eqs = [Eq(parse_expr(equation_part.split('=')[0].strip(), evaluate=True),
                                parse_expr(equation_part.split('=')[1].strip(), evaluate=True))]
                        eqs = [eq.subs(subs) for eq in eqs]
                    
                    # If we have substitutions but no equations, create an expression to evaluate
                    if not eqs and subs:
                        expr = parse_expr(equation_part, evaluate=True)
                        result = expr.subs(subs)
                        return {
                            "tool": "sympy",
                            "input": prompt,
                            "result_text": str(result),
                            "result_latex": None,
                            "raw": {"substitution": str(subs), "result": str(result)}
                        }
                        
                except Exception as e:
                    return {"tool":"sympy",
                            "input": prompt,
                            "result_text": f"Error processing 'for' clause: {str(e)}",
                            "result_latex": None,
                            "raw": {}}
            else:
                # Original processing for standard equations
                parts = [p.strip() for p in prompt.split(";") if p.strip()]
                eqs, subs = [], {}
                for p in parts:
                    if "=" in p:
                        left, right = p.split("=", 1)
                        try:
                            left = left.strip()
                            right = right.strip()
                            left_expr = parse_expr(left, evaluate=True)
                            right_expr = parse_expr(right, evaluate=True)
                            if left.isalpha() and (right.replace(".","",1).replace("-","",1).isdigit() or 
                                                right.replace(' ', '').replace('-', '').replace('+', '').replace('*', '').isdigit()):
                                subs[left] = right_expr
                            else:
                                eqs.append(Eq(left_expr, right_expr))
                        except Exception as e:
                            return {"tool":"sympy",
                                    "input": prompt,
                                    "result_text": f"Error parsing equation: {str(e)}",
                                    "result_latex": None,
                                    "raw": {}}

            result_text, latex, raw = "Could not compute.", None, {}
            
            # If we have equations after processing, try to solve them
            if eqs:
                try:
                    # Get all variables from the equations
                    all_vars = set()
                    for eq in eqs:
                        all_vars.update(eq.free_symbols)
                    all_vars = list(all_vars)
                    
                    # Try to solve the system of equations
                    if all_vars:
                        sol = sympy_solve(eqs, *all_vars, dict=True)
                        if sol:
                            result_text = "\n".join([f"{k} = {v}" for s in sol for k, v in s.items()])
                            raw["solve"] = str(sol)
                except Exception as e:
                    result_text = f"SymPy error: {e}"

            # If we have substitutions but no equations, try to evaluate the expression
            if subs and (not eqs or result_text == "Could not compute."):
                try:
                    # If we have a single expression with variables to substitute
                    if len(parts) == 1 and '=' not in parts[0]:
                        expr = parse_expr(parts[0], evaluate=True)
                        result = expr.subs(subs)
                        result_text = str(result)
                        raw["evaluated"] = str(result)
                except Exception as e:
                    if result_text == "Could not compute.":
                        result_text = f"Evaluation error: {e}"

            # Format the final result
            if result_text == "Could not compute." and raw:
                result_text = "\n".join([f"{k}: {v}" for k, v in raw.items()])

            return {
                "tool": "sympy",
                "input": prompt,
                "result_text": result_text,
                "result_latex": latex,
                "raw": raw
            }
            
        except Exception as e:
            import traceback
            return {
                "tool": "sympy",
                "input": prompt,
                "result_text": f"Unexpected error: {str(e)}\n\n{traceback.format_exc()}",
                "result_latex": None,
                "raw": {}
            }

    def compute(self, prompt: str) -> Dict[str, Any]:
        wolfram = self._wolfram(prompt)
        if wolfram:
            return wolfram
        return self._sympy(prompt)
